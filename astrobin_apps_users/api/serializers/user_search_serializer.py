import logging

from drf_haystack.serializers import HaystackSerializer

from astrobin.search_indexes import UserIndex

log = logging.getLogger(__name__)


class UserSearchSerializer(HaystackSerializer):
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
        ]
