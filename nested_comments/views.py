# Django
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
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
from common.permissions import ReadOnly

# This app
from .forms import NestedCommentForm
from .models import NestedComment
from .permissions import IsOwnerOrReadOnly
from .serializers import *


class ContentTypeList(generics.ListAPIView):
    model = ContentType
    serializer_class = ContentTypeSerializer
    permission_classes = (ReadOnly,)


class ContentTypeDetail(generics.RetrieveAPIView):
    model = ContentType
    serializer_class = ContentTypeSerializer
    permission_classes = (ReadOnly,)


class UserList(generics.ListAPIView):
    """
    This view presents a list of all the users in the system.
    """
    model = User
    serializer_class = UserSerializer
    permission_classes = (ReadOnly,)


class UserDetail(generics.RetrieveAPIView):
    """
    This view presents a instance of one of the users in the system.
    """
    model = User
    serializer_class = UserSerializer
    permission_classes = (ReadOnly,)


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


class NestedCommentCreateView(AjaxableResponseMixin, CreateView):
    model = NestedComment
    form_class = NestedCommentForm

    def form_valid(self, form):
        comment = form.save(commit = False)
        content_type = get_object_or_404(ContentType, pk = self.kwargs.pop('content_type_id'))

        comment.author = self.request.user
        comment.content_object = get_object_or_404(content_type.model_class(), pk = self.kwargs.pop('object_id'))
        comment.save()

        return super(NestedCommentCreateView, self).form_valid(form)
