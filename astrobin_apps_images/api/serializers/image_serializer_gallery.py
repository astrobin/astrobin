from rest_framework.serializers import ModelSerializer
from astrobin.models import Image
from astrobin_apps_images.api.serializers import ImageSerializer


class ImageSerializerGallery(ImageSerializer):
    def to_representation(self, instance: Image):
        representation = ModelSerializer.to_representation(self, instance)

        # Set thumbnails
        thumbnails = self.get_thumbnails(instance)
        representation.update({'thumbnails': thumbnails})

        # Set key_value_tags if applicable
        key_value_tags = self.get_key_value_tags(instance)
        if key_value_tags:
            representation.update({'key_value_tags': key_value_tags})

        return representation

    def get_thumbnails(self, instance: Image):
        return [
            {
                'alias': 'regular',
                'id': instance.pk,
                'revision': 'final',
                'url': instance.thumbnail('regular', None, sync=True)
            }
        ]

    def get_key_value_tags(self, instance: Image):
        request = self.context.get('request', None)
        if request and request.user == instance.user and request.query_params.get('collection'):
            return ','.join(
                [f"{tag['key']}={tag['value']}" for tag in instance.keyvaluetags.all().values('key', 'value')]
            )
        return None

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
            'view_count',
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
