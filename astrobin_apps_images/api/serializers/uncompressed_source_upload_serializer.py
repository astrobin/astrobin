from rest_framework import serializers

from astrobin.models import Image
from astrobin_apps_images.models import UncompressedSourceUpload


class UncompressedSourceUploadSerializer(serializers.HyperlinkedModelSerializer):
    image = serializers.PrimaryKeyRelatedField(queryset=Image.objects_including_wip)

    class Meta:
        model = UncompressedSourceUpload
        fields = (
            'pk',
            'image',
            'uncompressed_source_file',
        )
