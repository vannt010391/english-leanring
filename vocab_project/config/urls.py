from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    index, login_view, register_view,
    dashboard_view, vocabulary_view, topics_view,
    learning_plans_view, study_view, practice_view, analytics_view
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/auth/', include('accounts.urls')),
    path('api/topics/', include('topics.urls')),
    path('api/vocabulary/', include('vocabulary.urls')),
    path('api/learning/', include('learning.urls')),

    # Frontend pages
    path('', index, name='index'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('vocabulary/', vocabulary_view, name='vocabulary_list'),
    path('topics/', topics_view, name='topics_list'),
    path('learning/', learning_plans_view, name='learning_plans'),
    path('learning/<int:plan_id>/study/', study_view, name='study'),
    path('practice/', practice_view, name='practice'),
    path('analytics/', analytics_view, name='analytics'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
