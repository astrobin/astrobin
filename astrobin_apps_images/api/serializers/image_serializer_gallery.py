from rest_framework.serializers import ModelSerializer

from astrobin.models import Image
from astrobin_apps_images.api.serializers import ImageSerializer
from astrobin_apps_images.api.serializers.image_revision_gallery_serializer import ImageRevisionGallerySerializer


class ImageSerializerGallery(ImageSerializer):
    def to_representation(self, instance: Image):
        representation = ModelSerializer.to_representation(self, instance)

        thumbnails = [
            {
                'alias': 'regular',
                'id': instance.pk,
                'revision': 'final',
                'url': instance.thumbnail('regular', None, sync=True)
            }
        ]

        representation.update({'thumbnails': thumbnails})

        return representation

    def get_revisions(self, instance: Image):
        if instance.is_final:
            revisions = instance.revisions.none()
        else:
            revisions = instance.revisions.filter(is_final=True, deleted__isnull=True)

        return ImageRevisionGallerySerializer(revisions, many=True).data

    class Meta(ImageSerializer.Meta):
        fields = (
            'pk',
            'hash',
            'title',
            'w',
            'h',
            'square_cropping',
            'revisions',
            'final_gallery_thumbnail',
        )
