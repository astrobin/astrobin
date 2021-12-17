from django.db.models import QuerySet

from astrobin.models import Image
from astrobin_apps_iotd.api.serializers.base_queue_serializer import BaseQueueSerializer
from astrobin_apps_iotd.models import IotdVote


class JudgementQueueSerializer(BaseQueueSerializer):
    def to_representation(self, instance: Image):
        representation = super().to_representation(instance)
        last_vote: QuerySet[IotdVote] = IotdVote.last_for_image(instance.pk)

        if last_vote:
            representation.update(
                {
                    'last_vote_timestamp': last_vote[0].date if last_vote.exists() else None
                }
            )

        return representation
