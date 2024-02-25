from django.db.models.signals import post_save
from django.dispatch import receiver

from astrobin.models import Image
from astrobin_apps_images.models import ThumbnailGroup
from astrobin_apps_images.services import ImageService


@receiver(post_save, sender=ThumbnailGroup)
def thumbnail_group_post_save(sender, instance: ThumbnailGroup, **kwargs):
    final = ImageService(instance.image).get_final_revision_label()
    if instance.revision == final and instance.gallery != instance.image.final_gallery_thumbnail:
        Image.objects_including_wip.filter(pk=instance.image_id).update(
            final_gallery_thumbnail=instance.gallery,
        )
