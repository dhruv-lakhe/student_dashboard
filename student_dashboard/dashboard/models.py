from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# Create your models here.

class Board(models.Model):
    """Main Kanban Board"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    
class Column(models.Model):
    
# """Kanban Columns (To Do, In Progress, Done, etc.)"""
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('done', 'Done'),
    ]

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='columns')
    title = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    order = models.IntegerField(default=0)
    color = models.CharField(max_length=20, default='primary')  # Bootstrap color classes

    class Meta:
        ordering = ['order']
        unique_together = ['board', 'order']

    def __str__(self):
        return f"{self.board.name} - {self.title}"

class Task(models.Model):
    """Individual Tasks/Cards in Kanban"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    column = models.ForeignKey(Column, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    
    # Task metadata
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    order = models.IntegerField(default=0)
    
    # Dates
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Study-specific fields
    subject = models.CharField(max_length=100, blank=True)
    estimated_time = models.IntegerField(help_text="Estimated time in minutes", null=True, blank=True)
    actual_time = models.IntegerField(help_text="Actual time spent in minutes", null=True, blank=True)
    
    # Tags for categorization
    tags = models.ManyToManyField('Tag', blank=True, related_name='tasks')
    
    class Meta:
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def is_overdue(self):
        if self.due_date and self.completed_at is None:
            return self.due_date < timezone.now().date()
        return False

class Tag(models.Model):
    """Tags for categorizing tasks"""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=20, default='secondary')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags')
    
    def __str__(self):
        return self.name

class TaskComment(models.Model):
    """Comments on tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"

class TaskAttachment(models.Model):
    """File attachments for tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task_attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.filename} - {self.task.title}"

class Checklist(models.Model):
    """Subtasks within a task"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='checklist_items')
    title = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.title} ({'✓' if self.is_completed else '○'})"
    
    
class StudySession(models.Model):
    """Link Pomodoro sessions to tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='study_sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    duration = models.IntegerField(help_text="Duration in minutes")
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField()
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.task.title} ({self.duration}min)"
