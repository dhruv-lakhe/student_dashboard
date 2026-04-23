from django.contrib import admin

from .models import (Board, Checklist, Column, StudySession, Tag, Task,
                     TaskAttachment, TaskComment)


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at', 'user']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Board Information', {
            'fields': ('name', 'description', 'user', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ['title', 'board', 'status', 'order', 'color', 'task_count']
    list_filter = ['status', 'board']
    search_fields = ['title', 'board__name']
    ordering = ['board', 'order']
    
    def task_count(self, obj):
        return obj.tasks.count()
    task_count.short_description = 'Tasks'

class ChecklistInline(admin.TabularInline):
    model = Checklist
    extra = 1
    fields = ['title', 'is_completed', 'order']
    ordering = ['order']

class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0
    fields = ['user', 'comment', 'created_at']
    readonly_fields = ['created_at']

class TaskAttachmentInline(admin.TabularInline):
    model = TaskAttachment
    extra = 0
    fields = ['filename', 'file', 'uploaded_by', 'uploaded_at']
    readonly_fields = ['uploaded_at']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'column', 'user', 'priority', 'subject', 'due_date', 
                    'is_overdue_status', 'estimated_time', 'actual_time', 'created_at']
    list_filter = ['priority', 'column__status', 'subject', 'due_date', 'created_at']
    search_fields = ['title', 'description', 'user__username', 'subject']
    filter_horizontal = ['tags']
    readonly_fields = ['created_at', 'updated_at', 'is_overdue_status']
    inlines = [ChecklistInline, TaskCommentInline, TaskAttachmentInline]
    
    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'column', 'user')
        }),
        ('Priority & Status', {
            'fields': ('priority', 'order')
        }),
        ('Dates', {
            'fields': ('due_date', 'completed_at', 'created_at', 'updated_at', 'is_overdue_status')
        }),
        ('Study Details', {
            'fields': ('subject', 'estimated_time', 'actual_time')
        }),
        ('Categorization', {
            'fields': ('tags',)
        }),
    )
    
    def is_overdue_status(self, obj):
        if obj.is_overdue:
            return '❌ Overdue'
        return '✅ On Time'
    is_overdue_status.short_description = 'Status'
    
    actions = ['mark_as_completed', 'mark_as_high_priority']
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(completed_at=timezone.now())
        self.message_user(request, f'{updated} task(s) marked as completed.')
    mark_as_completed.short_description = 'Mark selected tasks as completed'
    
    def mark_as_high_priority(self, request, queryset):
        updated = queryset.update(priority='high')
        self.message_user(request, f'{updated} task(s) marked as high priority.')
    mark_as_high_priority.short_description = 'Set priority to High'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'user', 'task_count']
    list_filter = ['color', 'user']
    search_fields = ['name']
    
    def task_count(self, obj):
        return obj.tasks.count()
    task_count.short_description = 'Tasks'

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'comment_preview', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['comment', 'task__title', 'user__username']
    readonly_fields = ['created_at']
    
    def comment_preview(self, obj):
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment'

@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'task', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at', 'uploaded_by']
    search_fields = ['filename', 'task__title']
    readonly_fields = ['uploaded_at']

@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ['title', 'task', 'is_completed', 'order', 'created_at']
    list_filter = ['is_completed', 'created_at']
    search_fields = ['title', 'task__title']
    ordering = ['task', 'order']
    
    actions = ['mark_completed', 'mark_incomplete']
    
    def mark_completed(self, request, queryset):
        updated = queryset.update(is_completed=True)
        self.message_user(request, f'{updated} checklist item(s) marked as completed.')
    mark_completed.short_description = 'Mark as completed'
    
    def mark_incomplete(self, request, queryset):
        updated = queryset.update(is_completed=False)
        self.message_user(request, f'{updated} checklist item(s) marked as incomplete.')
    mark_incomplete.short_description = 'Mark as incomplete'

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'duration', 'started_at', 'ended_at']
    list_filter = ['user', 'started_at']
    search_fields = ['task__title', 'user__username', 'notes']
    readonly_fields = ['started_at', 'ended_at']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('task', 'user', 'duration')
        }),
        ('Time', {
            'fields': ('started_at', 'ended_at')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )
        