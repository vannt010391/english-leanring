from django.db import models
from django.conf import settings
from topics.models import Topic


class Vocabulary(models.Model):
    SOURCE_CHOICES = [
        ('system', 'System'),
        ('manual', 'Manual'),
        ('context', 'Context'),
        ('csv', 'CSV'),
    ]

    LEARNING_STATUS_CHOICES = [
        ('new', 'New'),
        ('learning', 'Learning'),
        ('mastered', 'Mastered'),
    ]

    CREATED_BY_ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('learner', 'Learner'),
    ]

    LEVEL_CHOICES = [
        ('A1', 'A1 - Beginner'),
        ('A2', 'A2 - Elementary'),
        ('B1', 'B1 - Intermediate'),
        ('B2', 'B2 - Upper Intermediate'),
        ('C1', 'C1 - Advanced'),
        ('C2', 'C2 - Proficiency'),
    ]

    TYPE_CHOICES = [
        ('noun', 'Noun'),
        ('verb', 'Verb'),
        ('adjective', 'Adjective'),
        ('adverb', 'Adverb'),
        ('preposition', 'Preposition'),
        ('conjunction', 'Conjunction'),
        ('pronoun', 'Pronoun'),
        ('interjection', 'Interjection'),
        ('phrase', 'Phrase'),
        ('idiom', 'Idiom'),
        ('other', 'Other'),
    ]

    word = models.CharField(max_length=255)
    meaning = models.TextField()
    meaning_vi = models.TextField(blank=True, null=True, verbose_name='Vietnamese Meaning')
    phonetics = models.CharField(max_length=255, blank=True, null=True)
    word_type = models.CharField(max_length=20, choices=TYPE_CHOICES, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    example_sentence = models.TextField(blank=True, null=True)
    level = models.CharField(max_length=2, choices=LEVEL_CHOICES, blank=True, null=True)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='manual')
    is_system = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vocab_created'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='vocabularies'
    )
    created_by_role = models.CharField(
        max_length=10,
        choices=CREATED_BY_ROLE_CHOICES,
        default='learner'
    )
    learning_status = models.CharField(
        max_length=10,
        choices=LEARNING_STATUS_CHOICES,
        default='new'
    )
    topics = models.ManyToManyField(
        Topic,
        through='VocabularyTopic',
        related_name='vocabularies'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vocabularies'
        ordering = ['-created_at']
        verbose_name_plural = 'vocabularies'

    def __str__(self):
        return self.word


class VocabularyTopic(models.Model):
    vocabulary = models.ForeignKey(Vocabulary, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)

    class Meta:
        db_table = 'vocabulary_topics'
        unique_together = ['vocabulary', 'topic']
