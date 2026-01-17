from django.db import models
from django.conf import settings


class LearningPlan(models.Model):
    """
    A Learning Plan represents a structured vocabulary learning schedule created by a learner.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_plans'
    )
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    daily_study_time = models.PositiveIntegerField(help_text='Minutes per day')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    selected_levels = models.JSONField(default=list)  # ['A1', 'B1', ...]
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # M2M relationships
    selected_topics = models.ManyToManyField(
        'topics.Topic',
        related_name='learning_plans'
    )
    vocabulary_snapshot = models.ManyToManyField(
        'vocabulary.Vocabulary',
        through='LearningPlanVocabulary',
        related_name='in_learning_plans'
    )

    class Meta:
        db_table = 'learning_plans'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.user.username}"

    @property
    def total_days(self):
        """FR-LP-05: Calculate total number of days in the plan."""
        return (self.end_date - self.start_date).days + 1

    @property
    def words_per_day(self):
        """Calculate recommended words per day based on total vocabulary."""
        total_words = self.vocabulary_snapshot.count()
        if self.total_days > 0:
            return max(1, total_words // self.total_days)
        return total_words


class LearningPlanVocabulary(models.Model):
    """
    Junction table tracking per-user, per-plan vocabulary status.
    This enables each learner to have their own learning status for each word within a plan.
    """
    LEARNING_STATUS_CHOICES = [
        ('new', 'New'),
        ('learned', 'Learned'),
        ('mastered', 'Mastered'),
        ('review_required', 'Review Required'),
    ]

    learning_plan = models.ForeignKey(
        LearningPlan,
        on_delete=models.CASCADE,
        related_name='plan_vocabulary'
    )
    vocabulary = models.ForeignKey(
        'vocabulary.Vocabulary',
        on_delete=models.CASCADE,
        related_name='plan_entries'
    )

    # Per-user status for this vocabulary in this plan
    status = models.CharField(
        max_length=20,
        choices=LEARNING_STATUS_CHOICES,
        default='new'
    )

    # User notes specific to this plan
    user_note = models.TextField(blank=True, null=True)

    # Tracking
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    review_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'learning_plan_vocabulary'
        unique_together = ['learning_plan', 'vocabulary']

    def __str__(self):
        return f"{self.vocabulary.word} in {self.learning_plan.name}"


class LearningProgress(models.Model):
    """
    Daily progress tracking per learning plan.
    Records how many words were studied each day.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_progress'
    )
    learning_plan = models.ForeignKey(
        LearningPlan,
        on_delete=models.CASCADE,
        related_name='daily_progress'
    )
    date = models.DateField()

    # Daily statistics
    words_studied = models.PositiveIntegerField(default=0)
    words_mastered = models.PositiveIntegerField(default=0)
    words_review_required = models.PositiveIntegerField(default=0)
    study_time_minutes = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'learning_progress'
        unique_together = ['user', 'learning_plan', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.learning_plan.name} - {self.date}"


class LearningSession(models.Model):
    """
    Tracks active learning sessions for resume capability.
    Addresses NFR-LRN-01: Sessions resume correctly after page reload.
    """
    SESSION_TYPE_CHOICES = [
        ('flashcard_study', 'Flashcard Study'),
        ('practice', 'Practice'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='learning_sessions'
    )
    learning_plan = models.ForeignKey(
        LearningPlan,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES)

    # Session state stored as JSON for flexibility
    # Example: {"current_index": 5, "vocabulary_ids": [1, 2, 3], "completed_ids": [1, 2]}
    state = models.JSONField(default=dict)

    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'learning_sessions'
        ordering = ['-last_activity_at']

    def __str__(self):
        return f"{self.session_type} - {self.user.username} - {self.learning_plan.name}"


class PracticeSession(models.Model):
    """
    Records completed practice sessions with results.
    """
    PRACTICE_TYPE_CHOICES = [
        ('flashcard', 'Flashcard Practice'),
        ('english_input', 'English Word Input'),
        ('vietnamese_input', 'Vietnamese Meaning Input'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='practice_sessions'
    )
    learning_plan = models.ForeignKey(
        LearningPlan,
        on_delete=models.CASCADE,
        related_name='practice_sessions'
    )
    practice_type = models.CharField(max_length=20, choices=PRACTICE_TYPE_CHOICES)

    # Results
    total_questions = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)

    # Detailed results for post-practice self-evaluation
    # Example: [{"vocabulary_id": 1, "correct": true, "user_answer": "hello", "time_spent": 5.2}]
    results = models.JSONField(default=list)

    duration_seconds = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'practice_sessions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.practice_type} - {self.user.username} - {self.created_at}"

    @property
    def incorrect_answers(self):
        return self.total_questions - self.correct_answers

    @property
    def accuracy_rate(self):
        if self.total_questions == 0:
            return 0
        return round((self.correct_answers / self.total_questions) * 100, 1)


class LearnerAnalytics(models.Model):
    """
    Cached analytics per user per learning plan.
    Updated on-demand to not block learning/practice flows (NFR-AN-01).
    """
    RISK_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    learning_plan = models.ForeignKey(
        LearningPlan,
        on_delete=models.CASCADE,
        related_name='analytics',
        null=True,
        blank=True  # null = overall analytics
    )

    # Metrics
    study_streak = models.PositiveIntegerField(default=0)  # Consecutive study days
    longest_streak = models.PositiveIntegerField(default=0)
    mastery_rate = models.FloatField(default=0.0)  # Percentage 0-100
    review_frequency = models.FloatField(default=0.0)  # Average reviews per word

    # Risk assessment
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default='low')
    risk_factors = models.JSONField(default=list)
    # Example: ["missed_3_days", "low_mastery_15%", "high_review_ratio_60%"]

    # Tracking
    last_study_date = models.DateField(null=True, blank=True)
    total_words_mastered = models.PositiveIntegerField(default=0)
    total_practice_sessions = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'learner_analytics'
        unique_together = ['user', 'learning_plan']

    def __str__(self):
        plan_name = self.learning_plan.name if self.learning_plan else 'Overall'
        return f"Analytics - {self.user.username} - {plan_name}"


class Notification(models.Model):
    """
    Notifications for risk alerts, reminders, and encouragement.
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('study_reminder', 'Study Reminder'),
        ('review_suggestion', 'Review Suggestion'),
        ('risk_alert', 'Risk Alert'),
        ('encouragement', 'Encouragement'),
        ('streak_achievement', 'Streak Achievement'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField()

    # Related entities
    learning_plan = models.ForeignKey(
        LearningPlan,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} - {self.user.username} - {self.title}"
