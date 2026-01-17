from rest_framework import serializers
from django.db.models import Q, Count

from .models import (
    LearningPlan, LearningPlanVocabulary, LearningProgress,
    LearningSession, PracticeSession, LearnerAnalytics, Notification
)
from topics.serializers import TopicSerializer
from topics.models import Topic
from vocabulary.models import Vocabulary
from vocabulary.serializers import VocabularyListSerializer


class LearningPlanVocabularySerializer(serializers.ModelSerializer):
    """Serializer for vocabulary items within a learning plan."""
    vocabulary = VocabularyListSerializer(read_only=True)

    class Meta:
        model = LearningPlanVocabulary
        fields = ['id', 'vocabulary', 'status', 'user_note', 'last_reviewed_at', 'review_count']


class FlashcardSerializer(serializers.ModelSerializer):
    """Serializer for flashcard display with vocabulary details."""
    word = serializers.CharField(source='vocabulary.word', read_only=True)
    meaning = serializers.CharField(source='vocabulary.meaning', read_only=True)
    meaning_vi = serializers.CharField(source='vocabulary.meaning_vi', read_only=True)
    phonetics = serializers.CharField(source='vocabulary.phonetics', read_only=True)
    word_type = serializers.CharField(source='vocabulary.word_type', read_only=True)
    example_sentence = serializers.CharField(source='vocabulary.example_sentence', read_only=True)
    level = serializers.CharField(source='vocabulary.level', read_only=True)
    vocabulary_id = serializers.IntegerField(source='vocabulary.id', read_only=True)

    class Meta:
        model = LearningPlanVocabulary
        fields = [
            'id', 'vocabulary_id', 'word', 'meaning', 'meaning_vi', 'phonetics',
            'word_type', 'example_sentence', 'level', 'status', 'user_note',
            'last_reviewed_at', 'review_count'
        ]


class LearningPlanListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing learning plans."""
    selected_topics = TopicSerializer(many=True, read_only=True)
    vocabulary_count = serializers.SerializerMethodField()
    progress_summary = serializers.SerializerMethodField()
    total_days = serializers.IntegerField(read_only=True)

    class Meta:
        model = LearningPlan
        fields = [
            'id', 'name', 'start_date', 'end_date', 'daily_study_time',
            'status', 'selected_topics', 'selected_levels', 'vocabulary_count',
            'progress_summary', 'total_days', 'created_at'
        ]

    def get_vocabulary_count(self, obj):
        return obj.vocabulary_snapshot.count()

    def get_progress_summary(self, obj):
        stats = LearningPlanVocabulary.objects.filter(
            learning_plan=obj
        ).values('status').annotate(count=Count('id'))
        return {item['status']: item['count'] for item in stats}


class LearningPlanDetailSerializer(serializers.ModelSerializer):
    """Full serializer for learning plan details."""
    selected_topics = TopicSerializer(many=True, read_only=True)
    vocabulary_count = serializers.SerializerMethodField()
    progress_summary = serializers.SerializerMethodField()
    total_days = serializers.IntegerField(read_only=True)
    words_per_day = serializers.IntegerField(read_only=True)

    class Meta:
        model = LearningPlan
        fields = [
            'id', 'name', 'start_date', 'end_date', 'daily_study_time',
            'status', 'selected_topics', 'selected_levels', 'vocabulary_count',
            'progress_summary', 'total_days', 'words_per_day', 'created_at', 'updated_at'
        ]

    def get_vocabulary_count(self, obj):
        return obj.vocabulary_snapshot.count()

    def get_progress_summary(self, obj):
        stats = LearningPlanVocabulary.objects.filter(
            learning_plan=obj
        ).values('status').annotate(count=Count('id'))
        return {item['status']: item['count'] for item in stats}


class LearningPlanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating learning plans."""
    topic_ids = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        many=True,
        write_only=True
    )
    selected_levels = serializers.ListField(
        child=serializers.ChoiceField(choices=['A1', 'A2', 'B1', 'B2', 'C1', 'C2']),
        min_length=1
    )

    class Meta:
        model = LearningPlan
        fields = ['name', 'start_date', 'end_date', 'daily_study_time', 'topic_ids', 'selected_levels']

    def validate(self, data):
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError({
                "end_date": "End date must be after start date."
            })
        return data

    def create(self, validated_data):
        topic_ids = validated_data.pop('topic_ids')
        user = self.context['request'].user

        plan = LearningPlan.objects.create(
            user=user,
            **validated_data
        )
        plan.selected_topics.set(topic_ids)

        # Create vocabulary snapshot based on selected topics and levels (FR-LP-04)
        vocabulary = Vocabulary.objects.filter(
            Q(is_system=True) | Q(owner=user),
            topics__in=topic_ids,
            level__in=validated_data['selected_levels']
        ).distinct()

        for vocab in vocabulary:
            LearningPlanVocabulary.objects.create(
                learning_plan=plan,
                vocabulary=vocab,
                status='new'
            )

        return plan


class LearningPlanUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating learning plans."""

    class Meta:
        model = LearningPlan
        fields = ['name', 'start_date', 'end_date', 'daily_study_time', 'status']

    def validate(self, data):
        start_date = data.get('start_date', self.instance.start_date)
        end_date = data.get('end_date', self.instance.end_date)
        if end_date <= start_date:
            raise serializers.ValidationError({
                "end_date": "End date must be after start date."
            })
        return data


class VocabularyStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating vocabulary status in a learning plan."""
    status = serializers.ChoiceField(
        choices=['new', 'learned', 'mastered', 'review_required']
    )
    user_note = serializers.CharField(required=False, allow_blank=True)


class LearningProgressSerializer(serializers.ModelSerializer):
    """Serializer for daily learning progress."""

    class Meta:
        model = LearningProgress
        fields = ['id', 'date', 'words_studied', 'words_mastered', 'words_review_required', 'study_time_minutes']
        read_only_fields = ['id']


class LearningSessionSerializer(serializers.ModelSerializer):
    """Serializer for learning session state."""
    learning_plan_name = serializers.CharField(source='learning_plan.name', read_only=True)

    class Meta:
        model = LearningSession
        fields = [
            'id', 'learning_plan', 'learning_plan_name', 'session_type',
            'state', 'is_active', 'started_at', 'last_activity_at'
        ]
        read_only_fields = ['id', 'started_at', 'last_activity_at']


class LearningSessionStateSerializer(serializers.Serializer):
    """Serializer for updating session state."""
    state = serializers.JSONField()


# Practice Serializers

class PracticeSessionStartSerializer(serializers.Serializer):
    """Serializer for starting a practice session."""
    learning_plan_id = serializers.IntegerField()
    practice_type = serializers.ChoiceField(
        choices=['flashcard', 'english_input', 'vietnamese_input']
    )
    word_count = serializers.IntegerField(default=10, min_value=1, max_value=100)


class PracticeQuestionSerializer(serializers.Serializer):
    """Serializer for practice questions."""
    id = serializers.IntegerField()
    vocabulary_id = serializers.IntegerField()
    prompt = serializers.CharField()
    hint = serializers.CharField(allow_null=True)
    word_type = serializers.CharField(allow_null=True)


class PracticeAnswerSerializer(serializers.Serializer):
    """Serializer for submitting practice answers."""
    vocabulary_id = serializers.IntegerField()
    user_answer = serializers.CharField()


class PracticeSessionCompleteSerializer(serializers.Serializer):
    """Serializer for completing a practice session with self-evaluation."""
    results = serializers.ListField(
        child=serializers.DictField()
    )
    duration_seconds = serializers.IntegerField(min_value=0)


class PracticeSessionListSerializer(serializers.ModelSerializer):
    """Serializer for listing practice sessions."""
    learning_plan_name = serializers.CharField(source='learning_plan.name', read_only=True)
    accuracy_rate = serializers.FloatField(read_only=True)
    incorrect_answers = serializers.IntegerField(read_only=True)

    class Meta:
        model = PracticeSession
        fields = [
            'id', 'learning_plan', 'learning_plan_name', 'practice_type',
            'total_questions', 'correct_answers', 'incorrect_answers',
            'accuracy_rate', 'duration_seconds', 'created_at'
        ]


class PracticeSessionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for practice session results."""
    learning_plan_name = serializers.CharField(source='learning_plan.name', read_only=True)
    accuracy_rate = serializers.FloatField(read_only=True)
    incorrect_answers = serializers.IntegerField(read_only=True)

    class Meta:
        model = PracticeSession
        fields = [
            'id', 'learning_plan', 'learning_plan_name', 'practice_type',
            'total_questions', 'correct_answers', 'incorrect_answers',
            'accuracy_rate', 'results', 'duration_seconds', 'created_at'
        ]


# Analytics Serializers

class LearnerAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for learner analytics."""
    learning_plan_name = serializers.CharField(
        source='learning_plan.name', read_only=True, allow_null=True
    )
    risk_factors_display = serializers.SerializerMethodField()

    class Meta:
        model = LearnerAnalytics
        fields = [
            'id', 'learning_plan', 'learning_plan_name', 'study_streak',
            'longest_streak', 'mastery_rate', 'review_frequency',
            'risk_level', 'risk_factors', 'risk_factors_display',
            'last_study_date', 'total_words_mastered', 'total_practice_sessions',
            'updated_at'
        ]

    def get_risk_factors_display(self, obj):
        """Convert risk factor codes to human-readable messages."""
        messages = {
            'missed': 'You have missed study days recently',
            'low_mastery': 'Your mastery rate is below target',
            'high_review': 'Many words need review',
            'no_practice': 'No practice sessions recently',
        }
        result = []
        for factor in obj.risk_factors:
            for key, msg in messages.items():
                if key in factor:
                    result.append(msg)
                    break
            else:
                result.append(factor)
        return result


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""
    learning_plan_name = serializers.CharField(
        source='learning_plan.name', read_only=True, allow_null=True
    )

    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message',
            'learning_plan', 'learning_plan_name', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'notification_type', 'title', 'message', 'learning_plan', 'created_at']
