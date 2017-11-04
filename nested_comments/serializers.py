# Third party apps
from rest_framework import serializers

# This app
from .models import NestedComment


class NestedCommentSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset = NestedComment.objects.all(),
        allow_null = True)

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
