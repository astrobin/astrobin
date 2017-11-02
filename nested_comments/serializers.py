# Third party apps
from rest_framework import serializers

# Other AstroBin apps
from common.api_fields import PKRelatedFieldAcceptNull

# This app
from .models import NestedComment


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
