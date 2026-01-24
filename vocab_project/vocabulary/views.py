import csv
import io

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from .models import Vocabulary, VocabularyTopic
from .serializers import (
    VocabularySerializer, VocabularyListSerializer, CSVImportSerializer,
    SystemVocabularySerializer
)
from topics.models import Topic
from accounts.permissions import IsOwnerOrAdmin, IsAdmin


class VocabularyPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class VocabularyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = VocabularyPagination

    def get_serializer_class(self):
        if self.action == 'list':
            return VocabularyListSerializer
        return VocabularySerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Vocabulary.objects.select_related('owner').prefetch_related('topics').order_by('word')

        if user.is_admin():
            base_queryset = queryset
        else:
            # Learners see only their own personal vocab (not system vocab)
            base_queryset = queryset.filter(
                Q(created_by=user) | Q(owner=user)
            )

        # Apply filters from query params
        search = self.request.query_params.get('search', '').strip()
        topic_id = self.request.query_params.get('topic', '')
        learning_status = self.request.query_params.get('status', '')
        word_type = self.request.query_params.get('word_type', '')
        level = self.request.query_params.get('level', '')

        if search:
            base_queryset = base_queryset.filter(
                Q(word__icontains=search) | Q(meaning__icontains=search)
            )

        if topic_id:
            base_queryset = base_queryset.filter(topics__id=topic_id)

        if learning_status:
            base_queryset = base_queryset.filter(learning_status=learning_status)

        if word_type:
            base_queryset = base_queryset.filter(word_type=word_type)

        if level:
            base_queryset = base_queryset.filter(level=level)

        return base_queryset.distinct()

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Learners can only update their own vocabulary
        if not request.user.is_admin() and instance.owner != request.user:
            return Response(
                {'error': 'You can only modify your own vocabulary.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Learners cannot modify system vocabulary
        if not request.user.is_admin() and instance.is_system:
            return Response(
                {'error': 'You cannot modify system vocabulary.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        # Learners can only delete their own vocabulary
        if not request.user.is_admin() and instance.owner != request.user:
            return Response(
                {'error': 'You can only delete your own vocabulary.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Learners cannot delete system vocabulary
        if not request.user.is_admin() and instance.is_system:
            return Response(
                {'error': 'You cannot delete system vocabulary.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def system(self, request):
        """Get all system vocabulary."""
        queryset = self.get_queryset().filter(is_system=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = VocabularyListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = VocabularyListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def personal(self, request):
        """Get user's personal vocabulary (created by the user)."""
        if request.user.is_admin():
            return Response(
                {'error': 'Admins do not have personal vocabulary.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        queryset = self.get_queryset().filter(
            Q(created_by=request.user) | Q(owner=request.user),
            is_system=False,
            created_by_role='learner'
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = VocabularyListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = VocabularyListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_topic(self, request):
        """Filter vocabulary by topic."""
        topic_id = request.query_params.get('topic_id')
        if not topic_id:
            return Response(
                {'error': 'topic_id parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        queryset = self.get_queryset().filter(topics__id=topic_id)
        serializer = VocabularyListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def import_csv(self, request):
        """Import vocabulary from CSV file."""
        serializer = CSVImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        csv_file = serializer.validated_data['file']
        topic_ids = serializer.validated_data.get('topic_ids', [])

        # Validate topics exist
        topics = []
        for topic_id in topic_ids:
            try:
                topic = Topic.objects.get(id=topic_id)
                topics.append(topic)
            except Topic.DoesNotExist:
                pass  # Ignore non-existent topics as per FR-CSV-04

        # Valid level and type choices
        valid_levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
        valid_types = ['noun', 'verb', 'adjective', 'adverb', 'preposition',
                       'conjunction', 'pronoun', 'interjection', 'phrase', 'idiom', 'other']

        try:
            decoded_file = csv_file.read().decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(decoded_file))

            created_count = 0
            updated_count = 0
            errors = []

            for row_num, row in enumerate(reader, start=2):
                try:
                    # Required fields
                    word = row.get('word', '').strip()
                    meaning = row.get('meaning', '').strip()

                    if not word or not meaning:
                        errors.append(f"Row {row_num}: 'word' and 'meaning' are required.")
                        continue

                    # Optional fields
                    meaning_vi = row.get('meaning_vi', row.get('viet_note', '')).strip() or None
                    phonetics = row.get('phonetics', '').strip() or None
                    note = row.get('note', '').strip() or None
                    example_sentence = row.get('example_sentence', row.get('example', '')).strip() or None

                    # Word type with validation
                    word_type = row.get('word_type', row.get('type', '')).strip().lower()
                    word_type = word_type if word_type in valid_types else None

                    # Level with validation
                    level = row.get('level', '').strip().upper()
                    level = level if level in valid_levels else None

                    # Check if word already exists (case-insensitive match)
                    try:
                        existing_vocab = Vocabulary.objects.filter(word__iexact=word).first()
                    except Exception:
                        # Fallback for SQLite: use case-sensitive lookup
                        existing_vocab = Vocabulary.objects.filter(word=word).first()

                    if existing_vocab:
                        # Word exists - just add new topics to it
                        vocab = existing_vocab
                        is_new = False
                    else:
                        # Create new vocabulary
                        if request.user.is_admin():
                            vocab = Vocabulary.objects.create(
                                word=word,
                                meaning=meaning,
                                meaning_vi=meaning_vi,
                                phonetics=phonetics,
                                word_type=word_type,
                                note=note,
                                example_sentence=example_sentence,
                                level=level,
                                source='csv',
                                is_system=True,
                                created_by_role='admin',
                                created_by=request.user,
                                owner=None
                            )
                        else:
                            vocab = Vocabulary.objects.create(
                                word=word,
                                meaning=meaning,
                                meaning_vi=meaning_vi,
                                phonetics=phonetics,
                                word_type=word_type,
                                note=note,
                                example_sentence=example_sentence,
                                level=level,
                                source='csv',
                                is_system=False,
                                created_by_role='learner',
                                created_by=request.user,
                                owner=request.user
                            )
                        is_new = True

                    # Assign topics from request (use get_or_create to avoid duplicates)
                    topics_added = False
                    for topic in topics:
                        _, created = VocabularyTopic.objects.get_or_create(
                            vocabulary=vocab, topic=topic
                        )
                        if created:
                            topics_added = True

                    # Check for topic column in CSV
                    csv_topic_names = row.get('topics', '').strip()
                    if csv_topic_names:
                        for topic_name in csv_topic_names.split(','):
                            topic_name = topic_name.strip()
                            try:
                                topic = Topic.objects.get(name__iexact=topic_name)
                                _, created = VocabularyTopic.objects.get_or_create(
                                    vocabulary=vocab, topic=topic
                                )
                                if created:
                                    topics_added = True
                            except Topic.DoesNotExist:
                                pass  # Ignore non-existent topics

                    if is_new:
                        created_count += 1
                    elif topics_added:
                        updated_count += 1

                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")

            message = f'Successfully imported {created_count} new vocabulary items.'
            if updated_count > 0:
                message += f' Updated topics for {updated_count} existing items.'

            return Response({
                'message': message,
                'created_count': created_count,
                'updated_count': updated_count,
                'errors': errors
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Failed to process CSV file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update the learning status of a vocabulary item."""
        vocabulary = self.get_object()
        new_status = request.data.get('learning_status')

        if new_status not in ['new', 'learning', 'mastered']:
            return Response(
                {'error': 'Invalid learning status. Choose from: new, learning, mastered'},
                status=status.HTTP_400_BAD_REQUEST
            )

        vocabulary.learning_status = new_status
        vocabulary.save()
        return Response(VocabularySerializer(vocabulary).data)

class SystemVocabularyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for admin to manage system/public vocabulary.
    Only admins can access this endpoint.
    """
    queryset = Vocabulary.objects.filter(is_system=True).select_related('owner').prefetch_related('topics').order_by('word')
    serializer_class = SystemVocabularySerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = VocabularyPagination

    def get_queryset(self):
        queryset = Vocabulary.objects.filter(is_system=True).select_related('owner').prefetch_related('topics').order_by('word')
        
        # Apply filters from query params
        search = self.request.query_params.get('search', '').strip()
        topic_id = self.request.query_params.get('topic', '')
        word_type = self.request.query_params.get('word_type', '')
        level = self.request.query_params.get('level', '')

        if search:
            queryset = queryset.filter(
                Q(word__icontains=search) | Q(meaning__icontains=search)
            )

        if topic_id:
            queryset = queryset.filter(topics__id=topic_id)

        if word_type:
            queryset = queryset.filter(word_type=word_type)

        if level:
            queryset = queryset.filter(level=level)

        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def import_csv(self, request):
        """Import system vocabulary from CSV file (admin only)."""
        serializer = CSVImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        csv_file = serializer.validated_data['file']
        topic_ids = serializer.validated_data.get('topic_ids', [])

        try:
            csv_data = csv.DictReader(io.StringIO(csv_file.read().decode('utf-8')))
            created_count = 0
            updated_count = 0
            errors = []

            for row_num, row in enumerate(csv_data, start=2):
                try:
                    word = row.get('word', '').strip()
                    meaning = row.get('meaning', '').strip()
                    meaning_vi = row.get('meaning_vi', '').strip() or None
                    phonetics = row.get('phonetics', '').strip() or None
                    word_type = row.get('word_type', '').strip() or None
                    level = row.get('level', '').strip() or None
                    note = row.get('note', '').strip() or None
                    example_sentence = row.get('example_sentence', '').strip() or None

                    if not word or not meaning:
                        errors.append(f"Row {row_num}: Missing required fields (word and meaning)")
                        continue

                    # Check if vocabulary exists (case-insensitive with fallback)
                    try:
                        existing_vocab = Vocabulary.objects.filter(word__iexact=word, is_system=True).first()
                    except:
                        existing_vocab = Vocabulary.objects.filter(word=word, is_system=True).first()

                    if existing_vocab:
                        # Update existing
                        existing_vocab.meaning = meaning
                        existing_vocab.meaning_vi = meaning_vi
                        existing_vocab.phonetics = phonetics
                        existing_vocab.word_type = word_type
                        existing_vocab.level = level
                        existing_vocab.note = note
                        existing_vocab.example_sentence = example_sentence
                        existing_vocab.save()
                        updated_count += 1
                    else:
                        # Create new
                        vocabulary = Vocabulary.objects.create(
                            word=word,
                            meaning=meaning,
                            meaning_vi=meaning_vi,
                            phonetics=phonetics,
                            word_type=word_type,
                            level=level,
                            note=note,
                            example_sentence=example_sentence,
                            is_system=True,
                            created_by_role='admin',
                            source='csv',
                            owner=None
                        )
                        created_count += 1

                    # Add topics if provided
                    if topic_ids:
                        for topic_id in topic_ids:
                            topic = Topic.objects.get(id=topic_id)
                            VocabularyTopic.objects.get_or_create(
                                vocabulary=vocabulary if not existing_vocab else existing_vocab,
                                topic=topic
                            )

                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")

            message = f'Successfully imported {created_count} new system vocabulary items.'
            if updated_count > 0:
                message += f' Updated {updated_count} existing items.'

            return Response({
                'message': message,
                'created_count': created_count,
                'updated_count': updated_count,
                'errors': errors
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Failed to process CSV file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'])
    def delete_vocabulary(self, request, pk=None):
        """Delete a system vocabulary item."""
        vocabulary = self.get_object()
        vocabulary.delete()
        return Response({'message': 'Vocabulary deleted successfully'}, status=status.HTTP_204_NO_CONTENT)