from django.contrib import admin
from .models import Notification, UserNotification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'target_type', 'priority', 'is_sent', 'created_by', 'created_at']
    list_filter = ['target_type', 'priority', 'is_sent', 'created_at']
    search_fields = ['title', 'message']
    ordering = ['-created_at']
    filter_horizontal = ['specific_users']


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__username', 'notification__title']
    ordering = ['-created_at']
