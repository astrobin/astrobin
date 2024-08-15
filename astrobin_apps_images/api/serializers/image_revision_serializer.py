from rest_framework import serializers

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

    def to_representation(self, instance: Image):
        representation = super().to_representation(instance)
        representation.update({
            'thumbnails': [
                {
                    'alias': alias,
                    'id': instance.pk,
                    'revision': instance.label,
                    'url': instance.thumbnail(alias, sync=True)
                } for alias in ('gallery', 'story', 'regular', 'hd', 'qhd')
            ]
        })
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
