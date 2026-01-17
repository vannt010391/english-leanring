from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VocabularyViewSet

router = DefaultRouter()
router.register('', VocabularyViewSet, basename='vocabulary')

urlpatterns = [
    path('', include(router.urls)),
]
