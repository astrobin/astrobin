from django.urls import reverse
from rest_framework import serializers

from astrobin.models import Image


class ImageFancyboxSerializer(serializers.ModelSerializer):
    hash = serializers.PrimaryKeyRelatedField(read_only=True)

    def to_representation(self, instance: Image):
        representation = super().to_representation(instance)

        representation.update(
            {
                'url': instance.get_absolute_url(),
                'src': reverse('image_rawthumb', kwargs={'id': instance.get_id(), 'r': 'final', 'alias': 'qhd'}),
                'thumb': reverse(
                    'image_rawthumb', kwargs={'id': instance.get_id(), 'r': 'final', 'alias': 'gallery'}
                ),
                'caption': f'{instance.user.userprofile.get_display_name()} - "{instance.title}"',
                'slug': instance.get_id(),
                'userId': instance.user.pk,
            }
        )

        return representation

    class Meta:
        model = Image
        fields = (
            'user',
            'pk',
            'hash',
            'title',
        )
