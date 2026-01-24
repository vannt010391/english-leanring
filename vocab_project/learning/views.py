import random
from datetime import date

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from .models import (
    LearningPlan, LearningPlanVocabulary, LearningProgress,
    LearningSession, PracticeSession, LearnerAnalytics, LearningNotification
)
from .serializers import (
    LearningPlanListSerializer, LearningPlanDetailSerializer,
    LearningPlanCreateSerializer, LearningPlanUpdateSerializer,
    LearningPlanVocabularySerializer, FlashcardSerializer,
    VocabularyStatusUpdateSerializer, LearningProgressSerializer,
    LearningSessionSerializer, LearningSessionStateSerializer,
    PracticeSessionStartSerializer, PracticeQuestionSerializer,
    PracticeSessionCompleteSerializer, PracticeSessionListSerializer,
    PracticeSessionDetailSerializer, LearnerAnalyticsSerializer,
    NotificationSerializer
)
from .services import AnalyticsService


class LearningPlanPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class FlashcardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class LearningPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for managing learning plans."""
    permission_classes = [IsAuthenticated]
    pagination_class = LearningPlanPagination

    def get_queryset(self):
        qs = LearningPlan.objects.filter(
            user=self.request.user
        ).prefetch_related('selected_topics')
        status_filter = self.request.query_params.get('status', '')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return LearningPlanCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return LearningPlanUpdateSerializer
        elif self.action == 'retrieve':
            return LearningPlanDetailSerializer
        return LearningPlanListSerializer

    def perform_update(self, serializer):
        plan = serializer.save()
        self._sync_daily_schedule(plan)
        return plan

    @action(detail=True, methods=['get'])
    def vocabulary(self, request, pk=None):
        """Get all vocabulary in this learning plan with their status."""
        plan = self.get_object()
        status_filter = request.query_params.get('status', '')
        search = request.query_params.get('search', '').strip()

        queryset = LearningPlanVocabulary.objects.filter(
            learning_plan=plan
        ).select_related('vocabulary').order_by('vocabulary__word')

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if search:
            queryset = queryset.filter(
                Q(vocabulary__word__icontains=search) |
                Q(vocabulary__meaning__icontains=search)
            )

        paginator = FlashcardPagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = LearningPlanVocabularySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = LearningPlanVocabularySerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def flashcards(self, request, pk=None):
        """Get flashcards for studying."""
        plan = self.get_object()
        status_filter = request.query_params.get('status', '')
        shuffle = request.query_params.get('shuffle', 'false').lower() == 'true'
        limit = request.query_params.get('limit', '')

        queryset = LearningPlanVocabulary.objects.filter(
            learning_plan=plan
        ).select_related('vocabulary')

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        else:
            # Default: prioritize new and review_required
            queryset = queryset.filter(status__in=['new', 'review_required', 'learned'])

        queryset = queryset.order_by('vocabulary__word')

        # Apply limit if specified
        if limit and limit.isdigit():
            limit_count = min(int(limit), 200)  # Max 200 cards per request
            queryset = queryset[:limit_count]

        items = list(queryset)

        if shuffle:
            random.shuffle(items)

        serializer = FlashcardSerializer(items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='vocabulary/(?P<vocab_id>[^/.]+)/status')
    def update_vocabulary_status(self, request, pk=None, vocab_id=None):
        """Update the learning status of a vocabulary item in this plan."""
        plan = self.get_object()

        try:
            plan_vocab = LearningPlanVocabulary.objects.get(
                learning_plan=plan,
                vocabulary_id=vocab_id
            )
        except LearningPlanVocabulary.DoesNotExist:
            return Response(
                {'error': 'Vocabulary not found in this plan.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = VocabularyStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_vocab.status = serializer.validated_data['status']
        if 'user_note' in serializer.validated_data:
            plan_vocab.user_note = serializer.validated_data['user_note']
        plan_vocab.last_reviewed_at = timezone.now()
        plan_vocab.review_count += 1
        plan_vocab.save()

        # Update daily progress
        self._update_daily_progress(plan, request.user, serializer.validated_data['status'])

        return Response(FlashcardSerializer(plan_vocab).data)

    def _update_daily_progress(self, plan, user, new_status):
        """Update or create daily progress record."""
        today = date.today()
        progress, created = LearningProgress.objects.get_or_create(
            user=user,
            learning_plan=plan,
            date=today,
            defaults={
                'words_studied': 0,
                'words_mastered': 0,
                'words_review_required': 0,
                'planned_words': plan.words_per_session,
                'status': 'upcoming'
            }
        )

        progress.words_studied += 1
        if new_status == 'mastered':
            progress.words_mastered += 1
        elif new_status == 'review_required':
            progress.words_review_required += 1

        # Mark completion if target reached
        target = progress.planned_words or plan.words_per_session
        if progress.words_studied >= target:
            progress.status = 'completed'
        progress.save()

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get daily progress for this learning plan."""
        plan = self.get_object()
        self._sync_daily_schedule(plan)

        qs = LearningProgress.objects.filter(
            learning_plan=plan,
            user=request.user
        ).order_by('date')

        days = request.query_params.get('days')
        if days and days.isdigit():
            days_int = int(days)
            qs = qs.order_by('-date')[:days_int]
            qs = qs.order_by('date')

        serializer = LearningProgressSerializer(qs, many=True)
        return Response(serializer.data)

    def _sync_daily_schedule(self, plan):
        today = date.today()
        # Remove old dates outside plan range
        LearningProgress.objects.filter(learning_plan=plan).exclude(
            date__range=(plan.start_date, plan.end_date)
        ).delete()

        current = plan.start_date
        while current <= plan.end_date:
            progress, _ = LearningProgress.objects.get_or_create(
                user=plan.user,
                learning_plan=plan,
                date=current,
                defaults={
                    'planned_words': plan.words_per_session,
                    'status': 'upcoming'
                }
            )

            # Keep planned_words aligned with plan settings
            progress.planned_words = plan.words_per_session

            if progress.words_studied >= progress.planned_words:
                progress.status = 'completed'
            else:
                progress.status = 'missed' if current < today else 'upcoming'

            progress.save()
            current += timedelta(days=1)

    @action(detail=True, methods=['post'])
    def start_session(self, request, pk=None):
        """Start or resume a learning session."""
        plan = self.get_object()

        # Check for existing active session
        existing_session = LearningSession.objects.filter(
            user=request.user,
            learning_plan=plan,
            session_type='flashcard_study',
            is_active=True
        ).first()

        if existing_session:
            # Return lightweight session info (without vocabulary_ids list)
            lightweight_state = {
                'current_index': existing_session.state.get('current_index', 0),
                'completed_ids': existing_session.state.get('completed_ids', []),
                'statuses': existing_session.state.get('statuses', {}),
                'started_at': existing_session.state.get('started_at')
            }
            return Response({
                'session': {
                    'id': existing_session.id,
                    'state': lightweight_state
                },
                'resumed': True
            })

        # Create new session (don't store all vocabulary IDs to keep state small)
        session = LearningSession.objects.create(
            user=request.user,
            learning_plan=plan,
            session_type='flashcard_study',
            state={
                'current_index': 0,
                'completed_ids': [],
                'statuses': {},
                'started_at': timezone.now().isoformat()
            }
        )

        return Response({
            'session': {
                'id': session.id,
                'state': session.state
            },
            'resumed': False
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'patch'])
    def session(self, request, pk=None):
        """Get or update session state."""
        plan = self.get_object()

        try:
            session = LearningSession.objects.get(
                user=request.user,
                learning_plan=plan,
                is_active=True
            )
        except LearningSession.DoesNotExist:
            return Response(
                {'error': 'No active session found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == 'GET':
            serializer = LearningSessionSerializer(session)
            return Response(serializer.data)

        # PATCH - update state
        state_serializer = LearningSessionStateSerializer(data=request.data)
        state_serializer.is_valid(raise_exception=True)

        session.state = state_serializer.validated_data['state']
        session.last_activity_at = timezone.now()
        session.save()

        serializer = LearningSessionSerializer(session)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """End a learning session."""
        plan = self.get_object()

        try:
            session = LearningSession.objects.get(
                user=request.user,
                learning_plan=plan,
                is_active=True
            )
        except LearningSession.DoesNotExist:
            return Response(
                {'error': 'No active session found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        session.is_active = False
        session.completed_at = timezone.now()
        session.save()

        # Update study time in progress
        if session.state.get('started_at'):
            from datetime import datetime
            start = datetime.fromisoformat(session.state['started_at'].replace('Z', '+00:00'))
            duration_minutes = int((timezone.now() - start).total_seconds() / 60)

            today = date.today()
            progress, _ = LearningProgress.objects.get_or_create(
                user=request.user,
                learning_plan=plan,
                date=today,
                defaults={'words_studied': 0, 'words_mastered': 0, 'words_review_required': 0}
            )
            progress.study_time_minutes += duration_minutes
            progress.save()

        return Response({'message': 'Session ended successfully.'})


class PracticeViewSet(viewsets.ViewSet):
    """ViewSet for practice sessions."""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """List completed practice sessions."""
        sessions = PracticeSession.objects.filter(
            user=request.user
        ).select_related('learning_plan').order_by('-created_at')[:50]

        serializer = PracticeSessionListSerializer(sessions, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Get practice session details."""
        try:
            session = PracticeSession.objects.get(id=pk, user=request.user)
        except PracticeSession.DoesNotExist:
            return Response(
                {'error': 'Practice session not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PracticeSessionDetailSerializer(session)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def start(self, request):
        """Start a new practice session."""
        serializer = PracticeSessionStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_id = serializer.validated_data['learning_plan_id']
        practice_type = serializer.validated_data['practice_type']
        word_count = serializer.validated_data['word_count']

        try:
            plan = LearningPlan.objects.get(id=plan_id, user=request.user)
        except LearningPlan.DoesNotExist:
            return Response(
                {'error': 'Learning plan not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get vocabulary for practice
        plan_vocabulary = list(LearningPlanVocabulary.objects.filter(
            learning_plan=plan
        ).select_related('vocabulary'))

        if not plan_vocabulary:
            return Response(
                {'error': 'No vocabulary in this learning plan.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Shuffle and limit
        random.shuffle(plan_vocabulary)
        selected = plan_vocabulary[:word_count]

        # Create practice session
        session = PracticeSession.objects.create(
            user=request.user,
            learning_plan=plan,
            practice_type=practice_type,
            total_questions=len(selected)
        )

        # Also create a learning session to track state
        LearningSession.objects.filter(
            user=request.user,
            learning_plan=plan,
            session_type='practice',
            is_active=True
        ).update(is_active=False)

        learning_session = LearningSession.objects.create(
            user=request.user,
            learning_plan=plan,
            session_type='practice',
            state={
                'practice_session_id': session.id,
                'practice_type': practice_type,
                'current_index': 0,
                'questions': self._generate_questions(selected, practice_type),
                'answers': [],
                'started_at': timezone.now().isoformat()
            }
        )

        return Response({
            'session_id': session.id,
            'learning_session_id': learning_session.id,
            'practice_type': practice_type,
            'questions': learning_session.state['questions'],
            'total_questions': len(selected)
        }, status=status.HTTP_201_CREATED)

    def _generate_questions(self, plan_vocabulary, practice_type):
        """Generate questions based on practice type."""
        questions = []

        for pv in plan_vocabulary:
            vocab = pv.vocabulary
            question = {
                'id': pv.id,
                'vocabulary_id': vocab.id,
                'word_type': vocab.word_type,
            }

            if practice_type == 'english_input':
                # Show Vietnamese, user types English
                question['prompt'] = vocab.meaning_vi or vocab.meaning
                question['hint'] = f"({vocab.word_type})" if vocab.word_type else None
                question['answer'] = vocab.word
            elif practice_type == 'vietnamese_input':
                # Show English, user types Vietnamese
                question['prompt'] = vocab.word
                question['hint'] = vocab.phonetics
                question['answer'] = vocab.meaning_vi or vocab.meaning
            else:  # flashcard
                question['prompt'] = vocab.word
                question['meaning'] = vocab.meaning
                question['meaning_vi'] = vocab.meaning_vi
                question['phonetics'] = vocab.phonetics
                question['example_sentence'] = vocab.example_sentence
                question['answer'] = None

            questions.append(question)

        return questions

    @action(detail=False, methods=['get', 'patch'])
    def state(self, request):
        """Get or update practice session state."""
        session = LearningSession.objects.filter(
            user=request.user,
            session_type='practice',
            is_active=True
        ).first()

        if not session:
            return Response(
                {'error': 'No active practice session.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method == 'GET':
            return Response({
                'session_id': session.state.get('practice_session_id'),
                'practice_type': session.state.get('practice_type'),
                'current_index': session.state.get('current_index', 0),
                'questions': session.state.get('questions', []),
                'answers': session.state.get('answers', []),
                'total_questions': len(session.state.get('questions', []))
            })

        # PATCH
        session.state.update(request.data.get('state', {}))
        session.last_activity_at = timezone.now()
        session.save()

        return Response({'message': 'State updated.'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a practice session with results."""
        try:
            session = PracticeSession.objects.get(id=pk, user=request.user)
        except PracticeSession.DoesNotExist:
            return Response(
                {'error': 'Practice session not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PracticeSessionCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        results = serializer.validated_data['results']
        duration = serializer.validated_data['duration_seconds']

        # Process results and update vocabulary status
        correct = 0
        for result in results:
            vocab_id = result.get('vocabulary_id')
            is_correct = result.get('correct', False)
            self_eval = result.get('self_evaluation')

            if is_correct:
                correct += 1

            # Update vocabulary status based on self-evaluation
            if self_eval:
                try:
                    plan_vocab = LearningPlanVocabulary.objects.get(
                        learning_plan=session.learning_plan,
                        vocabulary_id=vocab_id
                    )
                    plan_vocab.status = self_eval
                    plan_vocab.last_reviewed_at = timezone.now()
                    plan_vocab.review_count += 1
                    plan_vocab.save()
                except LearningPlanVocabulary.DoesNotExist:
                    pass

        session.correct_answers = correct
        session.results = results
        session.duration_seconds = duration
        session.save()

        # End the learning session
        LearningSession.objects.filter(
            user=request.user,
            session_type='practice',
            is_active=True
        ).update(is_active=False, completed_at=timezone.now())

        # Update daily progress
        today = date.today()
        progress, _ = LearningProgress.objects.get_or_create(
            user=request.user,
            learning_plan=session.learning_plan,
            date=today,
            defaults={'words_studied': 0, 'words_mastered': 0, 'words_review_required': 0}
        )
        progress.words_studied += session.total_questions
        progress.study_time_minutes += duration // 60
        progress.save()

        return Response(PracticeSessionDetailSerializer(session).data)


class AnalyticsViewSet(viewsets.ViewSet):
    """ViewSet for learner analytics."""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Get overall analytics for the user."""
        analytics = AnalyticsService.get_or_create_analytics(request.user)
        serializer = LearnerAnalyticsSerializer(analytics)

        # Get summary stats
        plan_count = LearningPlan.objects.filter(user=request.user, status='active').count()
        total_words = LearningPlanVocabulary.objects.filter(
            learning_plan__user=request.user
        ).count()
        mastered_words = LearningPlanVocabulary.objects.filter(
            learning_plan__user=request.user,
            status='mastered'
        ).count()

        return Response({
            'analytics': serializer.data,
            'summary': {
                'active_plans': plan_count,
                'total_words': total_words,
                'mastered_words': mastered_words,
            }
        })

    @action(detail=False, methods=['get'], url_path='plans/(?P<plan_id>[^/.]+)')
    def plan_analytics(self, request, plan_id=None):
        """Get analytics for a specific learning plan."""
        try:
            plan = LearningPlan.objects.get(id=plan_id, user=request.user)
        except LearningPlan.DoesNotExist:
            return Response(
                {'error': 'Learning plan not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        analytics = AnalyticsService.get_or_create_analytics(request.user, plan)
        serializer = LearnerAnalyticsSerializer(analytics)

        # Get plan-specific stats
        total_words = plan.vocabulary_snapshot.count()
        status_counts = LearningPlanVocabulary.objects.filter(
            learning_plan=plan
        ).values('status').annotate(count=Count('id'))

        return Response({
            'analytics': serializer.data,
            'vocabulary_stats': {
                'total': total_words,
                'by_status': {item['status']: item['count'] for item in status_counts}
            }
        })

    @action(detail=False, methods=['get'])
    def streak(self, request):
        """Get current study streak."""
        analytics = AnalyticsService.get_or_create_analytics(request.user)
        return Response({
            'current_streak': analytics.study_streak,
            'longest_streak': analytics.longest_streak,
            'last_study_date': analytics.last_study_date
        })

    @action(detail=False, methods=['get'])
    def risk(self, request):
        """Get risk assessment."""
        analytics = AnalyticsService.get_or_create_analytics(request.user)
        return Response({
            'risk_level': analytics.risk_level,
            'risk_factors': analytics.risk_factors,
            'recommendations': AnalyticsService.get_recommendations(analytics)
        })


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for notifications."""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return LearningNotification.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = LearningNotification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        return Response({'count': count})

    @action(detail=True, methods=['patch'])
    def read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        LearningNotification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True)
        return Response({'message': 'All notifications marked as read.'})


# Import Count for analytics
from django.db.models import Count
