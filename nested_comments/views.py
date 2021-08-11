from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .models import NestedComment
from .permissions import IsOwnerOrReadOnly
from .serializers import NestedCommentSerializer


class NestedCommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that represents a list of nested comments.
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

    @action(detail=True, methods=['post'])
    def approve(self, request, pk):
        comment = get_object_or_404(self.get_queryset(), pk=pk)  # type: NestedComment
        content_type = comment.content_type

        try:
            target = content_type.get_object_for_this_type(pk=comment.object_id)
        except content_type.model_class().DoesNotExist:
            raise Http404

        if content_type.model == 'image':
            user = target.user
            if request.user != user:
                raise PermissionDenied()

            self.get_queryset().filter(pk=pk).update(
                pending_moderation=False,
                moderator=request.user,
            )
        else:
            raise APIException('Unsupported content object model')

        return Response(status=200)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk):
        comment = get_object_or_404(self.get_queryset(), pk=pk)  # type: NestedComment
        content_type = comment.content_type

        try:
            target = content_type.get_object_for_this_type(pk=comment.object_id)
        except content_type.model_class().DoesNotExist:
            raise Http404

        if content_type.model == 'image':
            user = target.user
            if request.user != user:
                raise PermissionDenied()

            self.get_queryset().filter(pk=pk).update(
                pending_moderation=False,
                deleted=True,
                moderator=request.user,
            )
        else:
            raise APIException('Unsupported content object model')

        return Response(status=200)
