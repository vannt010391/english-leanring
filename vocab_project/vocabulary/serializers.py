from rest_framework import serializers
from .models import Vocabulary, VocabularyTopic
from topics.serializers import TopicSerializer
from topics.models import Topic


class VocabularySerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)
    topic_ids = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)

    class Meta:
        model = Vocabulary
        fields = [
            'id', 'word', 'meaning', 'meaning_vi', 'phonetics', 'word_type',
            'note', 'example_sentence', 'level', 'source',
            'is_system', 'owner', 'owner_username', 'created_by', 'created_by_username', 'created_by_role',
            'learning_status', 'topics', 'topic_ids', 'created_at'
        ]
        read_only_fields = ['id', 'owner', 'created_by', 'created_by_role', 'is_system', 'created_at']

    def create(self, validated_data):
        topic_ids = validated_data.pop('topic_ids', [])
        request = self.context.get('request')
        user = request.user

        if user.is_admin():
            validated_data['is_system'] = True
            validated_data['created_by_role'] = 'admin'
            validated_data['source'] = validated_data.get('source', 'system')
            validated_data['created_by'] = user
            validated_data['owner'] = None
        else:
            validated_data['is_system'] = False
            validated_data['created_by_role'] = 'learner'
            validated_data['source'] = validated_data.get('source', 'manual')
            validated_data['created_by'] = user
            validated_data['owner'] = user

        vocabulary = Vocabulary.objects.create(**validated_data)

        for topic in topic_ids:
            VocabularyTopic.objects.create(vocabulary=vocabulary, topic=topic)

        return vocabulary

    def update(self, instance, validated_data):
        topic_ids = validated_data.pop('topic_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if topic_ids is not None:
            instance.topics.clear()
            for topic in topic_ids:
                VocabularyTopic.objects.create(vocabulary=instance, topic=topic)

        return instance


class VocabularyListSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    owner_id = serializers.IntegerField(source='owner.id', read_only=True, allow_null=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True, allow_null=True)

    class Meta:
        model = Vocabulary
        fields = [
            'id', 'word', 'meaning', 'meaning_vi', 'phonetics', 'word_type',
            'note', 'example_sentence', 'level', 'is_system', 'learning_status',
            'topics', 'owner_id', 'owner_username', 'created_by_username', 'created_at'
        ]


class SystemVocabularySerializer(serializers.ModelSerializer):
    """Serializer for admin to manage system/public vocabulary"""
    topics = TopicSerializer(many=True, read_only=True)
    topic_ids = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    class Meta:
        model = Vocabulary
        fields = [
            'id', 'word', 'meaning', 'meaning_vi', 'phonetics', 'word_type',
            'note', 'example_sentence', 'level', 'topics', 'topic_ids', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        topic_ids = validated_data.pop('topic_ids', [])
        
        validated_data['is_system'] = True
        validated_data['created_by_role'] = 'admin'
        validated_data['source'] = 'system'
        validated_data['owner'] = None

        vocabulary = Vocabulary.objects.create(**validated_data)

        for topic in topic_ids:
            VocabularyTopic.objects.create(vocabulary=vocabulary, topic=topic)

        return vocabulary

    def update(self, instance, validated_data):
        topic_ids = validated_data.pop('topic_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if topic_ids is not None:
            instance.topics.clear()
            for topic in topic_ids:
                VocabularyTopic.objects.create(vocabulary=instance, topic=topic)

        return instance


class CSVImportSerializer(serializers.Serializer):
    file = serializers.FileField()
    topic_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[]
    )
