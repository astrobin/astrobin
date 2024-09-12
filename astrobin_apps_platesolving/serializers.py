from typing import Optional

from annoying.functions import get_object_or_None
from rest_framework import serializers

from astrobin.services.utils_service import UtilsService
from astrobin_apps_platesolving.models import (
    PlateSolvingAdvancedLiveLogEntry, PlateSolvingAdvancedSettings, PlateSolvingSettings, Solution,
    PlateSolvingAdvancedTask,
)


# DEPRECATION NOTE:
# Snake case keys are deprecated and will be removed eventually.
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

    def to_representation(self, instance: Solution):
        representation = super().to_representation(instance)

        if self.context.get('request') and 'include-pixinsight-details' in self.context['request'].query_params:
            representation['pixinsightQueueSize'] = self.get_pixinsight_queue_size(instance)
            representation['pixinsightStage'] = self.get_pixinsight_stage(instance)

        # Convert snake_case keys to camelCase and add them to the representation
        camel_case_representation = {}
        for key, value in representation.items():
            camel_case_key = UtilsService.snake_to_camel(key)
            camel_case_representation[camel_case_key] = value

        # Merge both snake_case and camelCase representations
        return {**representation, **camel_case_representation}

    def get_pixinsight_queue_size(self, obj: Solution) -> Optional[int]:
        task = get_object_or_None(PlateSolvingAdvancedTask, serial_number=obj.pixinsight_serial_number)
        if task is None:
            return None

        return PlateSolvingAdvancedTask.objects.filter(active=True, created__lt=task.created).count()

    def get_pixinsight_stage(self, obj: Solution) -> Optional[str]:
        live_log_entry = self._get_live_log_entry(obj)

        if live_log_entry:
            return live_log_entry.stage

        return None

    def _get_live_log_entry(self, obj: Solution) -> Optional[PlateSolvingAdvancedLiveLogEntry]:
        return PlateSolvingAdvancedLiveLogEntry.objects.filter(
            serial_number=obj.pixinsight_serial_number
        ).only(
            'stage', 'log'
        ).order_by(
            '-timestamp'
        ).first()


class AdvancedTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlateSolvingAdvancedTask
        fields = '__all__'


class PlateSolvingSettingsBaseSerializer(serializers.ModelSerializer):
    solution = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        fields = '__all__'


class PlateSolvingSettingsSerializer(PlateSolvingSettingsBaseSerializer):
    class Meta(PlateSolvingSettingsBaseSerializer.Meta):
        model = PlateSolvingSettings


class PlateSolvingAdvancedSettingsSerializer(PlateSolvingSettingsBaseSerializer):
    class Meta(PlateSolvingSettingsBaseSerializer.Meta):
        model = PlateSolvingAdvancedSettings


class PlateSolvingAdvancedSettingsSampleRawFrameFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlateSolvingAdvancedSettings
        fields = ('sample_raw_frame_file',)
