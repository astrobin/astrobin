from drf_haystack.serializers import HaystackSerializer

from astrobin.search_indexes import ForumPostIndex


class PostSearchSerializer(HaystackSerializer):
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
        ]
