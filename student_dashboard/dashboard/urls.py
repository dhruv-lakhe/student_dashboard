from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='signin', permanent=False), name='home'),
    path('recommender/', views.course_recommendation, name='recommender'),
    path('recommender/analyze/', views.course_recommendation, name='analyze_resume'),
    path('auth/login/', views.login_view, name='signin'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('kanban/', views.kanban_view, name='kanban'),
    path('kanban/new-task/', views.new_task, name='new_task'),
    path('kanban/task/<int:id>/edit/', views.edit_task, name='edit_task'),
    path('kanban/task/<int:id>/', views.view_task, name='view_task'),
    path('kanban/task/<int:id>/delete/', views.delete_task, name='delete_task'),
    path('pomodoro/', views.pomodoro_view, name='pomodoro'),
    path('kanban/complete-task/', views.complete_task_from_timer, name='complete_task_timer'),
]
