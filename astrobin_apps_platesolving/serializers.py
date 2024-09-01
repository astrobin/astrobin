from rest_framework import serializers

from astrobin_apps_platesolving.models import Solution, PlateSolvingAdvancedTask


class SolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solution
        read_only_fields = (
            'status',
            'submission_id',
            'pixinsight_serial_number',
            'content_type',
            'object_id',
            'image_file',
            'objects_in_field',
            'ra',
            'dec',
            'pixscale',
            'orientation',
            'radius',
            'advanced_ra',
            'advanced_dec',
            'advanced_pixscale',
            'advanced_orientation',
            'advanced_annotations',
        )
        exclude = [
            'advanced_matrix_rect',
            'advanced_matrix_delta',
            'advanced_ra_matrix',
            'advanced_dec_matrix',
        ]


class AdvancedTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlateSolvingAdvancedTask
        fields = '__all__'
