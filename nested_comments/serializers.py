from rest_framework import serializers

from common.serializers import AvatarField
from .models import NestedComment


class NestedCommentSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=NestedComment.objects.all(),
        allow_null=True)

    author_avatar = AvatarField(source='author', required=False)

    class Meta:
        model = NestedComment
        fields = (
            'id',
            'author',
            'author_avatar',
            'content_type',
            'object_id',
            'text',
            'created',
            'updated',
            'deleted',
            'parent',
        )
