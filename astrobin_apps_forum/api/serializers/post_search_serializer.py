from drf_haystack.serializers import HaystackSerializer
from rest_framework import serializers

from astrobin.search_indexes import ForumPostIndex


class PostSearchSerializer(HaystackSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        index_classes = [ForumPostIndex]
        fields = [
            'id',
            'text',
            'created',
            'updated',
            'topic_id',
            'topic_name',
            'user',
            'user_display_name',
            'user_avatar',
            'body_html',
        ]
