from rest_framework import serializers

from astrobin.models import Image
from astrobin_apps_images.models import KeyValueTag


class ImageSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    hash = serializers.PrimaryKeyRelatedField(read_only=True)
    w = serializers.IntegerField()
    h = serializers.IntegerField()
    key_value_tags = serializers.SerializerMethodField()

    def get_key_value_tags(self, image):
        return '\n'.join(["%s=%s" % (x.key, x.value) for x in KeyValueTag.objects.filter(image=image)])

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
            'part_of_group_set',
            'key_value_tags',
            'mouse_hover_image',
            'allow_comments',
        )
