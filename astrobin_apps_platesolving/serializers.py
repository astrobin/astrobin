from typing import Optional

from annoying.functions import get_object_or_None
from rest_framework import serializers

from astrobin_apps_platesolving.models import PlateSolvingAdvancedLiveLogEntry, Solution, PlateSolvingAdvancedTask


class SolutionSerializer(serializers.ModelSerializer):
    pixinsight_queue_size = serializers.SerializerMethodField(read_only=True)
    pixinsight_stage = serializers.SerializerMethodField(read_only=True)
    pixinsight_log = serializers.SerializerMethodField(read_only=True)

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
            'pixinsight_queue_size',
            'pixinsight_stage',
        )
        exclude = [
            'advanced_matrix_rect',
            'advanced_matrix_delta',
            'advanced_ra_matrix',
            'advanced_dec_matrix',
        ]

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

    def get_pixinsight_log(self, obj: Solution) -> Optional[str]:
        live_log_entry = self._get_live_log_entry(obj)

        if live_log_entry:
            return live_log_entry.log

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
