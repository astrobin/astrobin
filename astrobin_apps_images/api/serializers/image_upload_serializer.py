from rest_framework import serializers

from astrobin.models import Image
from astrobin_apps_images.models import KeyValueTag


class ImageUploadSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    hash = serializers.PrimaryKeyRelatedField(read_only=True)
    w = serializers.IntegerField()
    h = serializers.IntegerField()
    uploader_in_progress = serializers.NullBooleanField()

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
            'uploader_in_progress',
        )
