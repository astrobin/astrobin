import ast
import logging

from drf_haystack.serializers import HaystackSerializer

from astrobin.search_indexes import ImageIndex

log = logging.getLogger('apps')


class ImageSearchSerializer(HaystackSerializer):
    def to_representation(self, instance):
        ret = super().to_representation(instance)

        for prop in (
                'all_telescopes_2',
                'imaging_telescopes_2',
                'all_cameras_2',
                'imaging_cameras_2',
                'mounts_2',
                'filters_2',
                'accessories_2',
                'software_2',
                'guiding_telescopes_2',
                'guiding_cameras_2',

                'all_telescopes_2_id',
                'imaging_telescopes_2_id',
                'all_cameras_2_id',
                'imaging_cameras_2_id',
                'mounts_2_id',
                'filters_2_id',
                'accessories_2_id',
                'software_2_id',
                'guiding_telescopes_2_id',
                'guiding_cameras_2_id',
        ):
            if ret[prop]:
                ret[prop] = ast.literal_eval(ret[prop])

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

            'all_telescopes_2',
            'imaging_telescopes_2',
            'all_cameras_2',
            'imaging_cameras_2',
            'mounts_2',
            'filters_2',
            'accessories_2',
            'software_2',
            'guiding_telescopes_2',
            'guiding_cameras_2',

            'all_telescopes_2_id',
            'imaging_telescopes_2_id',
            'all_cameras_2_id',
            'imaging_cameras_2_id',
            'mounts_2_id',
            'filters_2_id',
            'accessories_2_id',
            'software_2_id',
            'guiding_telescopes_2_id',
            'guiding_cameras_2_id',

            'w',
            'h',
            'likes',
            'gallery_thumbnail',
        ]
