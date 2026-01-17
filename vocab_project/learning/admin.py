from django.contrib import admin
from .models import (
    LearningPlan, LearningPlanVocabulary, LearningProgress,
    LearningSession, PracticeSession, LearnerAnalytics, Notification
)


@admin.register(LearningPlan)
class LearningPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'status', 'start_date', 'end_date', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'user__username']
    filter_horizontal = ['selected_topics']


@admin.register(LearningPlanVocabulary)
class LearningPlanVocabularyAdmin(admin.ModelAdmin):
    list_display = ['vocabulary', 'learning_plan', 'status', 'review_count', 'last_reviewed_at']
    list_filter = ['status', 'learning_plan']
    search_fields = ['vocabulary__word', 'learning_plan__name']


@admin.register(LearningProgress)
class LearningProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'learning_plan', 'date', 'words_studied', 'words_mastered']
    list_filter = ['date', 'learning_plan']
    search_fields = ['user__username', 'learning_plan__name']


@admin.register(LearningSession)
class LearningSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'learning_plan', 'session_type', 'is_active', 'started_at', 'last_activity_at']
    list_filter = ['session_type', 'is_active']
    search_fields = ['user__username', 'learning_plan__name']


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'learning_plan', 'practice_type', 'total_questions', 'correct_answers', 'created_at']
    list_filter = ['practice_type', 'created_at']
    search_fields = ['user__username', 'learning_plan__name']


@admin.register(LearnerAnalytics)
class LearnerAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'learning_plan', 'study_streak', 'mastery_rate', 'risk_level', 'updated_at']
    list_filter = ['risk_level']
    search_fields = ['user__username']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title']
