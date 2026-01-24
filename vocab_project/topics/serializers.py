from rest_framework import serializers
from .models import Topic


class TopicSerializer(serializers.ModelSerializer):
    vocabulary_count = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)

    class Meta:
        model = Topic
        fields = ['id', 'name', 'description', 'created_at', 'created_by', 'created_by_username', 'vocabulary_count']
        read_only_fields = ['id', 'created_at', 'created_by', 'created_by_username']

    def get_vocabulary_count(self, obj):
        return obj.vocabularies.count()
