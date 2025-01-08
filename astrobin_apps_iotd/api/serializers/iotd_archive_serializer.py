from rest_framework import serializers

from astrobin_apps_images.api.serializers.image_serializer_gallery import ImageSerializerGallery
from astrobin_apps_iotd.models import Iotd


class IotdArchiveSerializer(serializers.ModelSerializer):
    image = ImageSerializerGallery(read_only=True)

    class Meta:
        model = Iotd
        exclude = ['judge']
