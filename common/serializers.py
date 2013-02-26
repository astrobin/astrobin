# Django
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

# Third party apps
from rest_framework import serializers


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username',)

