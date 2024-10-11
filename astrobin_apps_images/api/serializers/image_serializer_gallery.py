from rest_framework.serializers import ModelSerializer

from astrobin.models import Image
from astrobin_apps_images.api.serializers import ImageSerializer


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

    class Meta(ImageSerializer.Meta):
        fields = (
            'pk',
            'hash',
            'title',
            'is_wip',
            'w',
            'h',
            'square_cropping',
            'final_gallery_thumbnail',
            'published',
            'uploaded',
            'like_count',
            'bookmark_count',
            'comment_count',
            'username',
            'user_display_name',
            'is_iotd',
            'is_top_pick',
            'is_top_pick_nomination',
            'collaborators'
        )
