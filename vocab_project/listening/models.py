from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ListeningResource(models.Model):
    """Listening materials and exercises"""
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
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES)
    topic = models.CharField(max_length=100)
    
    # Audio file or URL
    audio_url = models.URLField(help_text="URL to audio file")
    duration = models.IntegerField(help_text="Duration in seconds")
    
    # Transcript
    transcript = models.TextField()
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['level', 'title']
        
    def __str__(self):
        return f"{self.level} - {self.title}"


class ListeningQuestion(models.Model):
    """Comprehension questions for listening exercises"""
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('fill_blank', 'Fill in the Blank'),
        ('short_answer', 'Short Answer'),
    ]
    
    resource = models.ForeignKey(ListeningResource, on_delete=models.CASCADE, related_name='questions')
    question = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    options = models.JSONField(default=list, help_text="Options for multiple choice")
    correct_answer = models.TextField()
    explanation = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['resource', 'order']
        
    def __str__(self):
        return f"{self.resource.title} - Q{self.order}"


class ListeningSession(models.Model):
    """Track listening practice sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listening_sessions')
    resource = models.ForeignKey(ListeningResource, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Playback tracking
    times_played = models.IntegerField(default=0)
    total_listen_time = models.IntegerField(default=0, help_text="Total seconds listened")
    
    # Quiz results
    score = models.IntegerField(null=True, blank=True)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-started_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.resource.title}"


class ListeningAnswer(models.Model):
    """Answers to listening comprehension questions"""
    session = models.ForeignKey(ListeningSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(ListeningQuestion, on_delete=models.CASCADE)
    user_answer = models.TextField()
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['answered_at']
        
    def __str__(self):
        return f"{self.session.user.username} - {self.question.question[:50]}"
