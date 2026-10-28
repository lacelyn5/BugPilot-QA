from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'priority', 'due_date', 'is_completed')
    list_filter = ('is_completed', 'priority', 'due_date', 'owner')
    search_fields = ('title', 'description', 'owner__username')
    ordering = ('due_date', '-id')
