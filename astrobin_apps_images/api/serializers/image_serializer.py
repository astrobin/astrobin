from rest_framework import serializers

from astrobin.models import Image, UserProfile
from astrobin_apps_images.api.fields import KeyValueTagsSerializerField


class ImageSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    hash = serializers.PrimaryKeyRelatedField(read_only=True)
    w = serializers.IntegerField()
    h = serializers.IntegerField()
    uploader_in_progress = serializers.NullBooleanField(read_only=True)
    key_value_tags = KeyValueTagsSerializerField(source='keyvaluetags')

    def update(self, instance, validated_data):
        instance = super(ImageSerializer, self).update(instance, validated_data)  # type: Image

        profile = instance.user.userprofile  # type: UserProfile

        if instance.watermark != profile.default_watermark or \
                instance.watermark_text != profile.default_watermark_text or \
                instance.watermark_position != profile.default_watermark_position or \
                instance.watermark_size != profile.default_watermark_size or \
                instance.watermark_opacity != profile.default_watermark_opacity:
            profile.default_watermark = instance.watermark
            profile.default_watermark_text = instance.watermark_text
            profile.default_watermark_position = instance.watermark_position
            profile.default_watermark_size = instance.watermark_size
            profile.default_watermark_opacity = instance.watermark_opacity
            profile.save(keep_deleted=True)

        return instance

    class Meta:
        model = Image
        fields = (
            'user',
            'pk',
            'hash',
            'title',
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
            'mouse_hover_image',
            'allow_comments',
            'uploader_in_progress',
            'square_cropping',
            'watermark',
            'watermark_text',
            'watermark_position',
            'watermark_size',
            'watermark_opacity',
            'sharpen_thumbnails',
            'key_value_tags',
            'locations',
            'full_size_display_limitation',
        )
