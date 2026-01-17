from django.shortcuts import render, redirect


def index(request):
    """Redirect to dashboard or login."""
    return redirect('dashboard')


def login_view(request):
    """Login page."""
    return render(request, 'auth/login.html')


def register_view(request):
    """Registration page."""
    return render(request, 'auth/register.html')


def dashboard_view(request):
    """Dashboard page."""
    return render(request, 'dashboard.html')


def vocabulary_view(request):
    """Vocabulary management page."""
    return render(request, 'vocabulary.html')


def topics_view(request):
    """Topics management page."""
    return render(request, 'topics.html')


def learning_plans_view(request):
    """Learning plans page."""
    return render(request, 'learning/plans.html')


def study_view(request, plan_id):
    """Flashcard study page."""
    return render(request, 'learning/study.html', {'plan_id': plan_id})


def practice_view(request):
    """Practice session page."""
    return render(request, 'learning/practice.html')


def analytics_view(request):
    """Analytics dashboard page."""
    return render(request, 'learning/analytics.html')
