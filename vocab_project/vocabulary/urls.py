from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VocabularyViewSet, SystemVocabularyViewSet

router = DefaultRouter()
router.register('', VocabularyViewSet, basename='vocabulary')
router.register('system', SystemVocabularyViewSet, basename='system-vocabulary')

urlpatterns = [
    path('', include(router.urls)),
]
