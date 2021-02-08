from rest_framework import serializers

from astrobin.models import Image


class ImageSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    hash = serializers.PrimaryKeyRelatedField(read_only=True)
    w = serializers.IntegerField()
    h = serializers.IntegerField()

    class Meta:
        model = Image
        fields = (
            'user',
            'pk',
            'hash',
            'title',
            'image_file',
            'is_wip',
            'skip_notifications',
            'w',
            'h',
            'imaging_telescopes',
            'imaging_cameras',
            'published',
            'license',
            'description',
            'link',
            'link_to_fits',
            'acquisition_type',
            'subject_type',
            'solar_system_main_subject',
            'data_source',
            'remote_source',
        )
