from django.db.models.signals import post_save
from django.dispatch import receiver

from astrobin_apps_iotd.models import IotdVote
from astrobin_apps_iotd.tasks import update_judgement_queues

@receiver(post_save, sender=IotdVote)
def iotd_vote_post_save(sender, instance: IotdVote, **kwargs):
    update_judgement_queues.delay()
