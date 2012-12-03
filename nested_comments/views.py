# Django
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.views.generic import *

# Third party apps
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from rest_framework.response import Response

# Other AstroBin apps
from common.mixins import AjaxableResponseMixin

# This app
from .forms import NestedCommentForm
from .models import NestedComment
from .serializers import *


class ContentTypeList(generics.ListAPIView):
    model = ContentType
    serializer_class = ContentTypeSerializer


class ContentTypeDetail(generics.RetrieveAPIView):
    model = ContentType
    serializer_class = ContentTypeSerializer


class UserList(generics.ListAPIView):
    """
    This view presents a list of all the users in the system.
    """
    model = User
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):
    """
    This view presents a instance of one of the users in the system.
    """
    model = User
    serializer_class = UserSerializer


class NestedCommentList(generics.ListCreateAPIView):
    """
    API endpoint that represents a list of nested comment.s
    """
    model = NestedComment
    serializer_class = NestedCommentSerializer
    filter_fields = ('content_type', 'object_id',)


class NestedCommentDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint that represents a single nested comment.
    """
    model = NestedComment
    serializer_class = NestedCommentSerializer


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
