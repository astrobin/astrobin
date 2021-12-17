from django.db.models import QuerySet

from astrobin.models import Image
from astrobin_apps_iotd.api.serializers.base_queue_serializer import BaseQueueSerializer
from astrobin_apps_iotd.models import IotdSubmission


class ReviewQueueSerializer(BaseQueueSerializer):
    def to_representation(self, instance: Image):
        representation = super().to_representation(instance)
        last_submission: QuerySet[IotdSubmission] = IotdSubmission.last_for_image(instance.pk)

        if last_submission:
            representation.update(
                {
                    'last_submission_timestamp': last_submission[0].date if last_submission.exists() else None
                }
        )

        return representation
