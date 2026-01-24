from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class WritingResource(models.Model):
    """Writing guides and sample essays"""
    LEVEL_CHOICES = [
        ('A1', 'A1 - Beginner'),
        ('A2', 'A2 - Elementary'),
        ('B1', 'B1 - Intermediate'),
        ('B2', 'B2 - Upper Intermediate'),
        ('C1', 'C1 - Advanced'),
        ('C2', 'C2 - Proficiency'),
    ]
    
    WRITING_TYPES = [
        ('essay', 'Essay'),
        ('letter', 'Letter'),
        ('email', 'Email'),
        ('report', 'Report'),
        ('article', 'Article'),
        ('review', 'Review'),
        ('story', 'Story'),
    ]
    
    title = models.CharField(max_length=255)
    writing_type = models.CharField(max_length=20, choices=WRITING_TYPES)
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES)
    topic = models.CharField(max_length=100)
    prompt = models.TextField(help_text="Writing prompt or question")
    sample_answer = models.TextField(help_text="Model answer")
    guidelines = models.TextField(help_text="Writing tips and structure")
    word_count = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['level', 'writing_type', 'title']
        
    def __str__(self):
        return f"{self.level} - {self.writing_type}: {self.title}"


class WritingSubmission(models.Model):
    """User writing practice submissions"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='writing_submissions')
    resource = models.ForeignKey(WritingResource, on_delete=models.CASCADE, related_name='submissions')
    content = models.TextField()
    word_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional self-evaluation
    self_rating = models.IntegerField(null=True, blank=True, help_text="Self-rating 1-5")
    notes = models.TextField(blank=True, help_text="Personal notes")
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.resource.title}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate word count
        if self.content:
            self.word_count = len(self.content.split())
        super().save(*args, **kwargs)
