import simplejson
from drf_haystack.serializers import HaystackSerializer

from astrobin.search_indexes import ImageIndex


class ImageSearchSerializer(HaystackSerializer):
    def to_representation(self, instance):
        ret = super().to_representation(instance)

        for prop in (
            'imaging_telescopes_2',
            'imaging_cameras_2',
            'mounts_2',
            'filters_2',
            'accessories_2',
            'software_2',
            'guiding_telescopes_2',
            'guiding_cameras_2',
        ):
            ret[prop] = simplejson.loads(ret[prop].replace('"', '\\"').replace('\'', '"'))

        return ret

    class Meta:
        index_classes = [ImageIndex]
        fields = [
            'object_id',
            'hash',
            'published',
            'title',
            'description',
            'imaging_telescopes_2',
            'imaging_cameras_2',
            'mounts_2',
            'filters_2',
            'accessories_2',
            'software_2',
            'guiding_telescopes_2',
            'guiding_cameras_2',
            'w',
            'h',
            'likes',
            'gallery_thumbnail',
        ]
