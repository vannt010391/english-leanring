from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LearningPlanViewSet, PracticeViewSet,
    AnalyticsViewSet, NotificationViewSet
)

router = DefaultRouter()
router.register('plans', LearningPlanViewSet, basename='learning-plan')
router.register('practice', PracticeViewSet, basename='practice')
router.register('analytics', AnalyticsViewSet, basename='analytics')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
