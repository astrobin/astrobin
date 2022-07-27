import logging

import simplejson
from drf_haystack.serializers import HaystackSerializer
from simplejson import JSONDecodeError

from astrobin.search_indexes import ImageIndex

log = logging.getLogger('apps')


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
            if ret[prop]:
                try:
                    ret[prop] = simplejson.loads(ret[prop].replace('"', '\\"').replace('\'', '"'))
                except JSONDecodeError as e:
                    log.warning(f'{ret[prop]} failed to parse as JSON')

        return ret

    class Meta:
        index_classes = [ImageIndex]
        fields = [
            'object_id',
            'text',
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
