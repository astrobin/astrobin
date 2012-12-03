# Django
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

# Third party apps
from rest_framework import serializers

# This app
from .models import NestedComment


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username',)


class NestedCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = NestedComment
        fields = (
            'id',
            'author',
            'content_type',
            'object_id',
            'text',
            'created',
            'updated',
            'deleted',
            'parent',
        )

