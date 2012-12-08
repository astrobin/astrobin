# Django
from django.shortcuts import get_object_or_404
from django.views.generic import *

# Third party apps
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework import permissions
from rest_framework.reverse import reverse
from rest_framework.response import Response

# Other AstroBin apps
from common.mixins import AjaxableResponseMixin

# This app
from .forms import NestedCommentForm
from .models import NestedComment
from .permissions import IsOwnerOrReadOnly
from .serializers import *


class NestedCommentList(generics.ListCreateAPIView):
    """
    API endpoint that represents a list of nested comment.s
    """
    model = NestedComment
    queryset = NestedComment.objects.order_by('pk')
    serializer_class = NestedCommentSerializer
    filter_fields = ('content_type', 'object_id',)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)

    def pre_save(self, obj):
        obj.author = self.request.user


class NestedCommentDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint that represents a single nested comment.
    """
    model = NestedComment
    serializer_class = NestedCommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)

    def pre_save(self, obj):
        obj.author = self.request.user

