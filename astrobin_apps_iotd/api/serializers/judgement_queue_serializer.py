from astrobin.models import Image
from astrobin_apps_iotd.api.serializers.base_queue_serializer import BaseQueueSerializer
from astrobin_apps_iotd.models import IotdVote


class JudgementQueueSerializer(BaseQueueSerializer):
    def to_representation(self, instance: Image):
        representation = super().to_representation(instance)
        last_vote: IotdVote = IotdVote.last_for_image(instance)

        if last_vote:
            representation.update(
                {
                    'last_vote_timestamp': last_vote.date
                }
            )

        return representation
