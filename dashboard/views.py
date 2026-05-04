import importlib
import json
import os
import tempfile
from datetime import date

import docx2txt
# Text extraction libraries
import pandas as pd
import PyPDF2
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from dashboard.recommendation import recommend_from_resume

from .models import Board, Column, Tag, Task


# --- Utility: Extract text from uploaded resume ---
def extract_text_from_resume(file):
    ext = os.path.splitext(file.name)[1].lower()
    text = ""

    if ext == '.pdf':
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    elif ext in ['.docx', '.doc']:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            for chunk in file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        text = docx2txt.process(tmp_path)
        os.remove(tmp_path)

    return text


# --- Main view: Handles both query string and resume upload ---
@csrf_exempt
def course_recommendation(request):
    query = request.GET.get('q', '')
    recommended_courses = []

    # Resume upload logic
    if request.method == "POST" and request.FILES.get('resume'):
        resume_file = request.FILES['resume']
        resume_text = extract_text_from_resume(resume_file)

        if resume_text.strip():
            # Use embedding to recommend courses
            recommended_courses = recommend_from_resume(resume_text)

    elif query:
        # Fallback: recommend from text input query
        recommended_courses = recommend_courses(query)

    # Convert DataFrame to list of dicts if needed
    if isinstance(recommended_courses, pd.DataFrame):
        recommended_courses = recommended_courses.to_dict(orient='records')

    # AJAX response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'courses': recommended_courses})

    # Normal render
    return render(request, 'dashboard/recommender/index.html', {
        'recommended_courses': recommended_courses,
        'query': query
    })



@login_required
def view_task(request, id):
    """Display task details using the same form template but read-only (is_view=True)."""
    task = get_object_or_404(Task, id=id, user=request.user)

    board = Board.objects.filter(user=request.user, is_active=True).first()
    if not board:
        messages.error(request, 'No board found.')
        return redirect('kanban')

    selected_tags = [str(t.id) for t in task.tags.all()]
    form_data = {
        'column': str(task.column.id),
        'title': task.title,
        'description': task.description,
        'priority': task.priority,
        'due_date': task.due_date.isoformat() if task.due_date else '',
        'subject': task.subject,
        'estimated_time': task.estimated_time if task.estimated_time is not None else '',
        'selected_tags': selected_tags
    }

    return render(request, 'dashboard/kb/new_task.html', {
        'columns': board.columns.all(),
        'user_tags': Tag.objects.filter(user=request.user),
        'today': date.today().isoformat(),
        'form_data': form_data,
        'is_view': True,
        'task_id': task.id
    })


@login_required
@require_POST
def delete_task(request, id):
    """Delete a task. Only POST allowed and only owner can delete."""
    task = get_object_or_404(Task, id=id, user=request.user)
    title = task.title
    try:
        task.delete()
        messages.success(request, f'Task "{title}" deleted.')
    except Exception as e:
        messages.error(request, f'Error deleting task: {str(e)}')

    return redirect('kanban')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username,password)
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        print("login")
        
        if user is not None:
            # Login the user
            login(request, user)
            # Redirect to dashboard or next page
            next_url = request.POST.get('next', '/')
            return redirect('dashboard')
        else:
            # Invalid credentials
            messages.error(request, 'Invalid username or password')
    
    return render(request, "dashboard/auth/sign-in.html")

@login_required
def logout_view(request):
    logout(request)
    return redirect('signin')

def register_view(request):
    """Register new user with email as both username and email"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')  # ← Fixed: use 'email' not 'username'
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        terms_accepted = request.POST.get('terms_accepted')
        
        # Validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
        elif not terms_accepted:
            messages.error(request, 'You must agree to the terms of use')
        # Check if email already registered
        elif User.objects.filter(username=email).exists():
            messages.error(request, 'This email is already registered')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered')
        else:
            # Create user with email as BOTH username and email
            user = User.objects.create_user(
                username=email,      # ← Email is the username
                email=email,         # ← Email is also in email field
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Signal automatically creates:
            # ✓ Board: "My Tasks"
            # ✓ 4 Columns: To Do, In Progress, Review, Done
            # ✓ 5 Tags: Assignment, Study, Exam, Project, Personal
            
            # Auto-login after registration
            login(request, user)
            
            messages.success(request, f'Welcome {first_name}! Your account has been created.')
            
            # Redirect to kanban board
            return redirect('dashboard')  # Change to your URL name
    
    return render(request, 'dashboard/auth/sign-up.html')

@login_required
def dashboard_view(request):
    user = request.user
    
    # Count tasks by column status using double underscore notation
    todo_count = Task.objects.filter(user=user, column__status='todo').count()
    in_progress_count = Task.objects.filter(user=user, column__status='in_progress').count()
    completed_count = Task.objects.filter(user=user, column__status='done').count()
    
    # Get recent tasks ordered by most recent first, limited to 5
    tasks = Task.objects.filter(user=user).select_related('column').order_by('-created_at')[:5]
    
    context = {
        'user': user,
        'todo_count': todo_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
        'tasks': tasks,
    }
    
    return render(request, "dashboard/dash/index.html", context)

@login_required
def kanban_view(request):
    """Main Kanban board view"""
    # Get user's board (auto-created by signal)
    board = Board.objects.filter(user=request.user, is_active=True).first()
    
      # If no board exists, create one with default columns
    if not board:
        # Create default board
        board = Board.objects.create(
            user=request.user,
            name="My Tasks",
            description="Your personal task management board",
            is_active=True
        )
        
        # Create 4 default columns
        Column.objects.create(board=board, title='To Do', status='todo', order=1, color='info')
        Column.objects.create(board=board, title='In Progress', status='in_progress', order=2, color='warning')
        Column.objects.create(board=board, title='Review', status='review', order=3, color='primary')
        Column.objects.create(board=board, title='Done', status='done', order=4, color='success')
    # Get all columns with their tasks
    # columns = board.columns.all()
    columns = board.columns.prefetch_related('tasks').all()
    # Pass to template
    context = {
        'board': board,
        'columns': columns,
    }

    return render(request, "dashboard/kb/kanban.html", {'columns': columns})

@login_required
def new_task(request):
    """Handle both form display and task creation"""
    board = Board.objects.filter(user=request.user, is_active=True).first()
    
    if not board:
        messages.error(request, 'No board found.')
        return redirect('kanban_view')
    
    if request.method == 'POST':
        # Get and validate form data
        column_id = request.POST.get('column')
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        priority = request.POST.get('priority', 'medium')
        due_date = request.POST.get('due_date') or None
        subject = request.POST.get('subject', '').strip()
        estimated_time = request.POST.get('estimated_time') or None
        tag_ids = request.POST.getlist('tags')
        
        errors = []
        
        # Validation
        if not column_id:
            errors.append('Please select a column.')
        else:
            try:
                column = Column.objects.get(id=column_id, board__user=request.user)
            except Column.DoesNotExist:
                errors.append('Invalid column selected.')
        
        if not title:
            errors.append('Task title is required.')
        elif len(title) > 200:
            errors.append('Title too long (max 200 characters).')
        
        if estimated_time:
            try:
                estimated_time = int(estimated_time)
                if estimated_time < 0:
                    errors.append('Estimated time must be positive.')
            except ValueError:
                errors.append('Invalid estimated time.')
        
        # If errors, redisplay form with preserved data
        if errors:
            for error in errors:
                messages.error(request, error)
            
            form_data = {
                'column': column_id,
                'title': title,
                'description': description,
                'priority': priority,
                'due_date': due_date,
                'subject': subject,
                'estimated_time': request.POST.get('estimated_time'),
                'selected_tags': tag_ids
            }
            
            return render(request, 'dashboard/kb/new_task.html', {
                'columns': board.columns.all(),
                'user_tags': Tag.objects.filter(user=request.user),
                'today': date.today().isoformat(),
                'form_data': form_data
            })
        
        # Create task
        try:
            max_order = Task.objects.filter(column=column).count()
            
            task = Task.objects.create(
                column=column,
                user=request.user,
                title=title,
                description=description,
                priority=priority,
                due_date=due_date,
                subject=subject,
                estimated_time=estimated_time,
                order=max_order
            )
            
            # Add tags
            if tag_ids:
                valid_tags = Tag.objects.filter(id__in=tag_ids, user=request.user)
                task.tags.set(valid_tags)
            
            # Success message with Pomodoro info
            success_msg = f'Task "{title}" created successfully!'
            if estimated_time:
                sessions = (estimated_time + 24) // 25
                success_msg += f' Estimated {sessions} 🍅 Pomodoro sessions.'
            
            messages.success(request, success_msg)
            return redirect('kanban')
            
        except Exception as e:
            messages.error(request, f'Error creating task: {str(e)}')
    
    # GET request - show empty form
    return render(request, 'dashboard/kb/new_task.html', {
        'columns': board.columns.all(),
        'user_tags': Tag.objects.filter(user=request.user),
        'today': date.today().isoformat(),
        'form_data': {}
    })


@login_required
def edit_task(request, id):
    """Edit an existing task. Reuses the new_task form template but pre-fills data and updates the Task on POST."""
    task = get_object_or_404(Task, id=id, user=request.user)

    board = Board.objects.filter(user=request.user, is_active=True).first()
    if not board:
        messages.error(request, 'No board found.')
        return redirect('kanban')

    if request.method == 'POST':
        # Similar validation as new_task
        column_id = request.POST.get('column')
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        priority = request.POST.get('priority', 'medium')
        due_date = request.POST.get('due_date') or None
        subject = request.POST.get('subject', '').strip()
        estimated_time = request.POST.get('estimated_time') or None
        tag_ids = request.POST.getlist('tags')

        errors = []

        if not column_id:
            errors.append('Please select a column.')
        else:
            try:
                column = Column.objects.get(id=column_id, board__user=request.user)
            except Column.DoesNotExist:
                errors.append('Invalid column selected.')

        if not title:
            errors.append('Task title is required.')
        elif len(title) > 200:
            errors.append('Title too long (max 200 characters).')

        if estimated_time:
            try:
                estimated_time = int(estimated_time)
                if estimated_time < 0:
                    errors.append('Estimated time must be positive.')
            except ValueError:
                errors.append('Invalid estimated time.')

        if errors:
            for error in errors:
                messages.error(request, error)

            form_data = {
                'column': column_id,
                'title': title,
                'description': description,
                'priority': priority,
                'due_date': due_date,
                'subject': subject,
                'estimated_time': request.POST.get('estimated_time'),
                'selected_tags': tag_ids
            }

            return render(request, 'dashboard/kb/new_task.html', {
                'columns': board.columns.all(),
                'user_tags': Tag.objects.filter(user=request.user),
                'today': date.today().isoformat(),
                'form_data': form_data,
                'is_edit': True,
                'task_id': task.id
            })

        # Update the task
        try:
            task.column = column
            task.title = title
            task.description = description
            task.priority = priority
            task.due_date = due_date
            task.subject = subject
            task.estimated_time = estimated_time
            task.save()

            # Update tags
            if tag_ids:
                valid_tags = Tag.objects.filter(id__in=tag_ids, user=request.user)
                task.tags.set(valid_tags)
            else:
                task.tags.clear()

            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect('kanban')

        except Exception as e:
            messages.error(request, f'Error updating task: {str(e)}')

    # GET - prefill form_data from task
    selected_tags = [str(t.id) for t in task.tags.all()]
    form_data = {
        'column': str(task.column.id),
        'title': task.title,
        'description': task.description,
        'priority': task.priority,
        'due_date': task.due_date.isoformat() if task.due_date else '',
        'subject': task.subject,
        'estimated_time': task.estimated_time if task.estimated_time is not None else '',
        'selected_tags': selected_tags
    }

    return render(request, 'dashboard/kb/new_task.html', {
        'columns': board.columns.all(),
        'user_tags': Tag.objects.filter(user=request.user),
        'today': date.today().isoformat(),
        'form_data': form_data,
        'is_edit': True,
        'task_id': task.id
    })
    

@login_required
def pomodoro_view(request):
    """Simple Pomodoro view - loads user's incomplete tasks.

    Changes:
    - Include incomplete tasks regardless of whether `estimated_time` is set so
      they appear in the selection list.
    - Read optional GET `task_id` and pass `selected_task_id` so template can
      pre-select the task when opened from Kanban.
    """
    # Optional preselected task id from querystring
    task_id = request.GET.get('task_id')
    selected_task_id = None
    if task_id:
        try:
            selected_task_id = int(task_id)
        except (ValueError, TypeError):
            selected_task_id = None

    # Get user's incomplete tasks (include those without estimated_time)
    tasks = Task.objects.filter(
        user=request.user,
        completed_at__isnull=True,  # Not completed
    ).select_related('column').order_by('-created_at')[:50]

    return render(request, "dashboard/pomodoro/pomodoro.html", {
        'tasks': tasks,
        'selected_task_id': selected_task_id
    })


@login_required
@require_POST
def complete_task_from_timer(request):
    """Mark task as complete from timer - ONLY endpoint needed"""
    try:
        data = json.loads(request.body)
        task_id = data.get('task_id')
        actual_time_minutes = data.get('actual_time_minutes', 0)

        # Get the task
        task = get_object_or_404(Task, id=task_id, user=request.user)

        # Update task
        task.actual_time = actual_time_minutes
        task.completed_at = timezone.now()

        # Move to done column if available
        done_column = Column.objects.filter(
            board__user=request.user,
            title__icontains='done'
        ).first() or Column.objects.filter(
            board__user=request.user,
            status='done'
        ).first()

        if done_column:
            task.column = done_column

        task.save()

        return JsonResponse({
            'success': True,
            'message': f'Task "{task.title}" completed with {actual_time_minutes} minutes of work!'
        })

    except Task.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Task not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })
        
        

