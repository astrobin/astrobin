from precise_bbcode.bbcode import get_parser
from rest_framework import serializers

from common.serializers import AvatarField
from .models import NestedComment


class NestedCommentSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=NestedComment.objects.all(),
        allow_null=True)

    author_avatar = AvatarField(source='author', required=False)

    html = serializers.CharField(read_only=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        parser = get_parser()
        data["html"] = parser.render(instance.text)
        return data

    class Meta:
        model = NestedComment
        fields = (
            'id',
            'author',
            'author_avatar',
            'content_type',
            'object_id',
            'text',
            'html',
            'created',
            'updated',
            'deleted',
            'pending_moderation',
            'parent',
            'depth',
            'likes',
        )
