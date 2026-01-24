from django.contrib import admin
from .models import ListeningResource, ListeningQuestion, ListeningSession, ListeningAnswer


@admin.register(ListeningResource)
class ListeningResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'level', 'topic', 'duration', 'is_active', 'created_at']
    list_filter = ['level', 'is_active', 'created_at']
    search_fields = ['title', 'topic', 'description']
    ordering = ['level', 'title']


@admin.register(ListeningQuestion)
class ListeningQuestionAdmin(admin.ModelAdmin):
    list_display = ['resource', 'question_type', 'order']
    list_filter = ['question_type', 'resource__level']
    search_fields = ['question', 'resource__title']
    ordering = ['resource', 'order']


@admin.register(ListeningSession)
class ListeningSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource', 'score', 'times_played', 'total_listen_time', 'started_at']
    list_filter = ['started_at', 'completed_at']
    search_fields = ['user__username', 'resource__title']
    ordering = ['-started_at']


@admin.register(ListeningAnswer)
class ListeningAnswerAdmin(admin.ModelAdmin):
    list_display = ['session', 'question', 'is_correct', 'answered_at']
    list_filter = ['is_correct', 'answered_at']
    search_fields = ['session__user__username', 'question__question']
    ordering = ['-answered_at']
