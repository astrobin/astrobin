from annoying.functions import get_object_or_None
from django.apps import apps
from django.db.models.signals import pre_save, post_migrate
from django.dispatch import receiver
from notification import models as notification

from astrobin_apps_equipment.models import Camera
from astrobin_apps_equipment.notice_types import EQUIPMENT_NOTICE_TYPES


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


def create_notice_types(sender, **kwargs):
    for notice_type in EQUIPMENT_NOTICE_TYPES:
        notification.create_notice_type(notice_type[0], notice_type[1], notice_type[2], default=notice_type[3])


post_migrate.connect(create_notice_types, sender=apps.get_app_config('astrobin'))
