from django.contrib import admin
from .models import GrammarResource, GrammarExercise, GrammarPracticeSession, GrammarAnswer


@admin.register(GrammarResource)
class GrammarResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'level', 'topic', 'is_active', 'created_at']
    list_filter = ['level', 'is_active', 'created_at']
    search_fields = ['title', 'topic', 'description']
    ordering = ['level', 'topic', 'title']


@admin.register(GrammarExercise)
class GrammarExerciseAdmin(admin.ModelAdmin):
    list_display = ['resource', 'exercise_type', 'order']
    list_filter = ['exercise_type', 'resource__level']
    search_fields = ['question', 'resource__title']
    ordering = ['resource', 'order']


@admin.register(GrammarPracticeSession)
class GrammarPracticeSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource', 'score', 'correct_answers', 'total_questions', 'started_at', 'completed_at']
    list_filter = ['started_at', 'completed_at']
    search_fields = ['user__username', 'resource__title']
    ordering = ['-started_at']


@admin.register(GrammarAnswer)
class GrammarAnswerAdmin(admin.ModelAdmin):
    list_display = ['session', 'exercise', 'is_correct', 'answered_at']
    list_filter = ['is_correct', 'answered_at']
    search_fields = ['session__user__username', 'exercise__question']
    ordering = ['-answered_at']
