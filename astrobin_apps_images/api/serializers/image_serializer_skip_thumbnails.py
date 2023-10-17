from rest_framework.serializers import ModelSerializer

from astrobin.models import Image
from astrobin_apps_images.api.serializers import ImageSerializer


class ImageSerializerSkipThumbnails(ImageSerializer):
    def to_representation(self, instance: Image):
        representation = ModelSerializer.to_representation(self, instance)
        representation.update(self.acquisitions_representation(instance))
        return representation

    class Meta(ImageSerializer.Meta):
        pass
