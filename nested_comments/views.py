from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework import permissions

from .models import NestedComment
from .permissions import IsOwnerOrReadOnly
from .serializers import NestedCommentSerializer


class NestedCommentList(generics.ListCreateAPIView):
    """
    API endpoint that represents a list of nested comment.s
    """
    model = NestedComment
    queryset = NestedComment.objects.order_by('pk')
    serializer_class = NestedCommentSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('content_type', 'object_id',)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class NestedCommentDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint that represents a single nested comment.
    """
    model = NestedComment
    queryset = NestedComment.objects.all()
    serializer_class = NestedCommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
