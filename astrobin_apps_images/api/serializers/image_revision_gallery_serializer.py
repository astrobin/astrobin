from rest_framework.serializers import ModelSerializer

from astrobin.models import ImageRevision
from astrobin_apps_images.api.serializers import ImageRevisionSerializer


class ImageRevisionGallerySerializer(ImageRevisionSerializer):
    def to_representation(self, instance: ImageRevision):
        representation = ModelSerializer.to_representation(self, instance)

        thumbnails = [
            {
                'alias': 'regular',
                'id': instance.pk,
                'revision': instance.label,
                'url': instance.thumbnail('regular', sync=True)
            }
        ]

        representation.update({'thumbnails': thumbnails})

        return representation

    class Meta(ImageRevisionSerializer.Meta):
        fields = (
            'pk',
            'image',
            'label',
            'is_final',
            'w',
            'h',
            'square_cropping',
        )
