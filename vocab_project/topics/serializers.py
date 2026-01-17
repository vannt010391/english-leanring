from rest_framework import serializers
from .models import Topic


class TopicSerializer(serializers.ModelSerializer):
    vocabulary_count = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = ['id', 'name', 'description', 'created_at', 'vocabulary_count']
        read_only_fields = ['id', 'created_at']

    def get_vocabulary_count(self, obj):
        return obj.vocabularies.count()
