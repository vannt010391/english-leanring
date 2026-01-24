from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

from .models import Topic
from .serializers import TopicSerializer


class TopicViewSet(viewsets.ModelViewSet):
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin():
            return Topic.objects.all()
        return Topic.objects.filter(
            Q(created_by=user) | Q(created_by__role='admin')
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        topic = self.get_object()
        if not request.user.is_admin() and topic.created_by != request.user:
            return Response(
                {'error': 'You can only modify your own topics.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        topic = self.get_object()
        if not request.user.is_admin() and topic.created_by != request.user:
            return Response(
                {'error': 'You can only delete your own topics.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
