from datetime import datetime, timedelta

from rest_framework import serializers

from astrobin.enums.mouse_hover_image import MouseHoverImage
from astrobin.models import ImageRevision, Image
from astrobin_apps_platesolving.serializers import SolutionSerializer


class ImageRevisionSerializer(serializers.HyperlinkedModelSerializer):
    image = serializers.PrimaryKeyRelatedField(queryset=Image.objects_including_wip)
    label = serializers.CharField(max_length=2)
    is_final = serializers.BooleanField(default=False)
    w = serializers.IntegerField()
    h = serializers.IntegerField()
    uploader_in_progress = serializers.NullBooleanField()
    solution = SolutionSerializer(read_only=True)

    def to_representation(self, instance: ImageRevision):
        # Get the Image instance from context if provided
        image = self.context.get('image', None)
        if image:
            # Use the passed image instance instead of fetching it
            instance.image = image

        representation = super().to_representation(instance)

        thumbnails = [
            {
                'alias': alias,
                'id': instance.pk,
                'revision': instance.label,
                'url': instance.thumbnail(alias, sync=True)
            } for alias in ('gallery', 'story', 'regular', 'hd', 'qhd')
        ]

        if instance.mouse_hover_image == MouseHoverImage.INVERTED:
            thumbnails += [
                {
                    'alias': 'hd_inverted',
                    'id': instance.pk,
                    'revision': instance.label,
                    'url': instance.thumbnail('hd_inverted', sync=True)
                },
                {
                    'alias': 'qhd_inverted',
                    'id': instance.pk,
                    'revision': instance.label,
                    'url': instance.thumbnail('qhd_inverted', sync=True)
                }
            ]

        if (
                instance.is_final and
                instance.image.submitted_for_iotd_tp_consideration and
                instance.image.submitted_for_iotd_tp_consideration > datetime.now() - timedelta(days=60)
        ):
            # Add hd_anonymized only if it's available (for IOTD/TP queue purposes)
            thumbnail_group = instance.image.thumbnails.filter(
                revision=instance.label,
                hd_anonymized__isnull=False
            )
            if thumbnail_group.exists():
                thumbnails.append(
                    {
                        'alias': 'hd_anonymized',
                        'id': instance.pk,
                        'revision': instance.label,
                        'url': thumbnail_group.first().hd_anonymized
                    }
                )

        representation.update({'thumbnails': thumbnails})

        if instance.image_file and instance.image_file.name.lower().endswith('.gif'):
            representation.update({'image_file': instance.image_file.url})

        return representation

    class Meta:
        model = ImageRevision
        fields = (
            'pk',
            'uploaded',
            'image',
            'image_file',
            'title',
            'description',
            'skip_notifications',
            'skip_activity_stream',
            'label',
            'is_final',
            'w',
            'h',
            'uploader_in_progress',
            'uploader_upload_length',
            'constellation',
            'solution',
            'mouse_hover_image',
        )
