from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TopicViewSet

router = DefaultRouter()
router.register('', TopicViewSet, basename='topic')

urlpatterns = [
    path('', include(router.urls)),
]
