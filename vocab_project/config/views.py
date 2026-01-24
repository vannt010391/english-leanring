from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from functools import wraps

User = get_user_model()


def is_admin(user):
    """Check if user is admin."""
    return user.is_authenticated and user.is_admin()


def token_or_login_required(view_func):
    """Decorator that allows authentication via session, token header, or token cookie."""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Check if user is already authenticated via session
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)
        
        # Check for token-based authentication via header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Token '):
            token_key = auth_header.split(' ')[1]
            try:
                token = Token.objects.get(key=token_key)
                request.user = token.user
                return view_func(request, *args, **kwargs)
            except Token.DoesNotExist:
                pass
        
        # Check for token in cookie
        token_key = request.COOKIES.get('auth_token')
        if token_key:
            try:
                token = Token.objects.get(key=token_key)
                request.user = token.user
                return view_func(request, *args, **kwargs)
            except Token.DoesNotExist:
                pass
        
        # If no valid authentication, redirect to login
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())
    
    return wrapped_view


def index(request):
    """Redirect to dashboard or login."""
    return redirect('dashboard')


def login_view(request):
    """Login page."""
    return render(request, 'auth/login.html')


def register_view(request):
    """Registration page."""
    return render(request, 'auth/register.html')


@token_or_login_required
def dashboard_view(request):
    """Dashboard page."""
    return render(request, 'dashboard.html')


@token_or_login_required
def vocabulary_view(request):
    """Vocabulary management page."""
    return render(request, 'vocabulary.html')


@token_or_login_required
def topics_view(request):
    """Topics management page."""
    return render(request, 'topics.html')


@token_or_login_required
def learning_plans_view(request):
    """Learning plans page."""
    return render(request, 'learning/plans.html')


@token_or_login_required
def study_view(request, plan_id):
    """Flashcard study page."""
    return render(request, 'learning/study.html', {'plan_id': plan_id})


@token_or_login_required
def practice_view(request):
    """Practice session page."""
    return render(request, 'learning/practice.html')


@token_or_login_required
def analytics_view(request):
    """Analytics dashboard page."""
    return render(request, 'learning/analytics.html')


@token_or_login_required
def admin_users_view(request):
    """Admin user management page."""
    if not is_admin(request.user):
        return redirect('dashboard')
    return render(request, 'admin/users.html')


@token_or_login_required
def admin_system_vocabulary_view(request):
    """Admin system vocabulary management page."""
    if not is_admin(request.user):
        return redirect('dashboard')
    return render(request, 'admin/system_vocabulary.html')


@token_or_login_required
def admin_vocabulary_management_view(request):
    """Admin vocabulary management page with same UI as vocabulary list."""
    if not is_admin(request.user):
        return redirect('dashboard')
    return render(request, 'admin/vocabulary_management.html')


@token_or_login_required
def admin_analytics_view(request):
    """Admin analytics dashboard page."""
    if not is_admin(request.user):
        return redirect('dashboard')
    return render(request, 'admin/analytics.html')
