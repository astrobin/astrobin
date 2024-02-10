from django.db.models.signals import post_save
from django.dispatch import receiver

from astrobin.models import Image
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.models import Iotd
from common.services import DateTimeService


@receiver(post_save, sender=Iotd)
def iotd_post_save(sender, instance: Iotd, created: bool, **kwargs):
    if created:
        Image.objects.filter(pk=instance.image.pk).update(updated=DateTimeService.now())
        ImageService(instance.image).clear_badges_cache()
