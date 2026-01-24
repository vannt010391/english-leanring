from django.contrib import admin
from .models import WritingResource, WritingSubmission


@admin.register(WritingResource)
class WritingResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'writing_type', 'level', 'topic', 'is_active', 'created_at']
    list_filter = ['writing_type', 'level', 'is_active', 'created_at']
    search_fields = ['title', 'topic', 'prompt']
    ordering = ['level', 'writing_type', 'title']


@admin.register(WritingSubmission)
class WritingSubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource', 'status', 'word_count', 'self_rating', 'created_at']
    list_filter = ['status', 'created_at', 'self_rating']
    search_fields = ['user__username', 'resource__title']
    ordering = ['-created_at']
