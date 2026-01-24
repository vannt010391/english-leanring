from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class GrammarResource(models.Model):
    """Grammar lessons and resources"""
    LEVEL_CHOICES = [
        ('A1', 'A1 - Beginner'),
        ('A2', 'A2 - Elementary'),
        ('B1', 'B1 - Intermediate'),
        ('B2', 'B2 - Upper Intermediate'),
        ('C1', 'C1 - Advanced'),
        ('C2', 'C2 - Proficiency'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    content = models.TextField(help_text="Full grammar lesson content")
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES)
    topic = models.CharField(max_length=100, help_text="e.g., Tenses, Articles, Modals")
    examples = models.JSONField(default=list, help_text="List of example sentences")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['level', 'topic', 'title']
        
    def __str__(self):
        return f"{self.level} - {self.title}"


class GrammarExercise(models.Model):
    """Grammar practice exercises"""
    EXERCISE_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('fill_blank', 'Fill in the Blank'),
        ('correction', 'Error Correction'),
        ('transformation', 'Sentence Transformation'),
    ]
    
    resource = models.ForeignKey(GrammarResource, on_delete=models.CASCADE, related_name='exercises')
    question = models.TextField()
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPES)
    options = models.JSONField(default=list, help_text="List of options for multiple choice")
    correct_answer = models.TextField()
    explanation = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['resource', 'order']
        
    def __str__(self):
        return f"{self.resource.title} - Q{self.order}"


class GrammarPracticeSession(models.Model):
    """Track user grammar practice sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grammar_sessions')
    resource = models.ForeignKey(GrammarResource, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True, help_text="Percentage score")
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-started_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.resource.title}"


class GrammarAnswer(models.Model):
    """Individual answers in a practice session"""
    session = models.ForeignKey(GrammarPracticeSession, on_delete=models.CASCADE, related_name='answers')
    exercise = models.ForeignKey(GrammarExercise, on_delete=models.CASCADE)
    user_answer = models.TextField()
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['answered_at']
        
    def __str__(self):
        return f"{self.session.user.username} - {self.exercise.question[:50]}"
