# Django
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.views.generic import *

# Third party apps
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework import permissions
from rest_framework.reverse import reverse
from rest_framework.response import Response

# This app
from .permissions import ReadOnly
from .serializers import *


class ContentTypeList(generics.ListAPIView):
    model = ContentType
    serializer_class = ContentTypeSerializer
    permission_classes = (ReadOnly,)
    filter_fields = ('app_label', 'model',)


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


