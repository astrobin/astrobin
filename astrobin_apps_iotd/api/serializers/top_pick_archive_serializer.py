from rest_framework import serializers

from astrobin_apps_images.api.serializers.image_serializer_gallery import ImageSerializerGallery
from astrobin_apps_iotd.models import TopPickArchive


class TopPickArchiveSerializer(serializers.ModelSerializer):
    image = ImageSerializerGallery(read_only=True)

    class Meta:
        model = TopPickArchive
        fields = '__all__'
