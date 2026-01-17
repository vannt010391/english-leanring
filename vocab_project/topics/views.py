from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Topic
from .serializers import TopicSerializer
from accounts.permissions import IsAdminOrReadOnly


class TopicViewSet(viewsets.ModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
