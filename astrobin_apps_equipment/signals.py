from annoying.functions import get_object_or_None
from django.db.models.signals import pre_save
from django.dispatch import receiver

from astrobin_apps_equipment.models import Camera


@receiver(pre_save, sender=Camera)
def mirror_modified_camera(sender, instance: Camera, **kwargs):
    if not instance.modified:
        before_saving = get_object_or_None(Camera, pk=instance.pk)
        if before_saving:
            Camera.objects.filter(brand=before_saving.brand, name=before_saving.name, modified=True).update(
                name=instance.name,
                image=instance.image,
                type=instance.type,
                sensor=instance.sensor,
                cooled=instance.cooled,
                max_cooling=instance.max_cooling,
                back_focus=instance.back_focus
            )
