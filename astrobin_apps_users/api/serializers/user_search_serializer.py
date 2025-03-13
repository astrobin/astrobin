import logging

from rest_framework import serializers
from drf_haystack.serializers import HaystackSerializer

from astrobin.search_indexes import UserIndex

log = logging.getLogger(__name__)


class UserSearchSerializer(HaystackSerializer):
    comments_received = serializers.SerializerMethodField()

    def get_comments_received(self, obj) -> int:
        return getattr(obj, 'comments', 0)

    class Meta:
        index_classes = [UserIndex]
        fields = [
            'username',
            'display_name',
            'avatar_url',
            'images',
            'total_likes_received',
            'followers',
            'contribution_index',
            'normalized_likes',
            'integration',
            'top_pick_nominations',
            'top_picks',
            'iotds',
            'normalized_likes',
            'comments_written',
            # Use a custom field because using 'comments' directly would raise an error:
            # AttributeError: 'ManyToOneRel' object has no attribute 'validators'
            'comments_received',
            'comment_likes_received',
            'forum_posts',
            'forum_post_likes_received',
            'contribution_index',
        ]
