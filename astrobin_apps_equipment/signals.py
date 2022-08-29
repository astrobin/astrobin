from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from annoying.functions import get_object_or_None
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate, post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from notification import models as notification
from pybb.models import Category, Forum
from safedelete.signals import post_softdelete

from astrobin.services.utils_service import UtilsService
from astrobin_apps_equipment.models import (
    Accessory, Camera, CameraEditProposal, EquipmentBrand, EquipmentItem, EquipmentPreset, Filter, Mount, Sensor,
    Software, Telescope,
)
from astrobin_apps_equipment.models.accessory_edit_proposal import AccessoryEditProposal
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_equipment.models.equipment_item import EquipmentItemReviewerDecision
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.models.filter_edit_proposal import FilterEditProposal
from astrobin_apps_equipment.models.mount_edit_proposal import MountEditProposal
from astrobin_apps_equipment.models.sensor_edit_proposal import SensorEditProposal
from astrobin_apps_equipment.models.software_edit_proposal import SoftwareEditProposal
from astrobin_apps_equipment.models.telescope_edit_proposal import TelescopeEditProposal
from astrobin_apps_equipment.notice_types import EQUIPMENT_NOTICE_TYPES
from astrobin_apps_notifications.utils import build_notification_url, push_notification
from common.constants import GroupName
from common.services import AppRedirectionService
from nested_comments.models import NestedComment


@receiver(post_migrate, sender=apps.get_app_config('astrobin'))
def create_notice_types(sender, **kwargs):
    for notice_type in EQUIPMENT_NOTICE_TYPES:
        notification.create_notice_type(notice_type[0], notice_type[1], notice_type[2], default=notice_type[3])


@receiver(post_save, sender=Camera)
def create_DSLR_mirrorless_camera_variants(sender, instance: Camera, created: bool, **kwargs):
    if not created or instance.type != CameraType.DSLR_MIRRORLESS:
        return

    properties = dict(
        klass = instance.klass,
        created_by = instance.created_by,
        brand = instance.brand,
        name = instance.name,
        website = instance.website,
        group = instance.group,
        image = instance.image,
        type = instance.type,
        sensor = instance.sensor,
        cooled = False,
        max_cooling = instance.max_cooling,
        back_focus = instance.back_focus,
    )

    just_modified, created = Camera.objects.get_or_create(**{**properties, 'modified': True, 'cooled': False})
    modified_and_cooled, created = Camera.objects.get_or_create(**{**properties, 'modified': True, 'cooled': True})
    just_cooled, created = Camera.objects.get_or_create(**{**properties, 'modified': False, 'cooled': True})

    Camera.objects.filter(
        pk__in=[x.pk for x in [just_modified, modified_and_cooled, just_cooled]]
    ).update(variant_of=instance)

@receiver(pre_save, sender=Camera)
def mirror_camera_update_to_variants(sender, instance: Camera, **kwargs):
    before_saving = get_object_or_None(Camera, pk=instance.pk)
    if before_saving:
        Camera.objects.filter(brand=before_saving.brand, name=before_saving.name).exclude(pk=instance.pk).update(
            reviewed_by=instance.reviewed_by,
            reviewed_timestamp=instance.reviewed_timestamp,
            reviewer_decision=instance.reviewer_decision,
            reviewer_rejection_reason=instance.reviewer_rejection_reason,
            reviewer_comment=instance.reviewer_comment,
            brand=instance.brand,
            name=instance.name,
            website=instance.website,
            community_notes=instance.community_notes,
            group=instance.group,
            image=instance.image,
            type=instance.type,
            sensor=instance.sensor,
            max_cooling=instance.max_cooling,
            back_focus=instance.back_focus,
            frozen_as_ambiguous=instance.frozen_as_ambiguous
        )


@receiver(post_softdelete, sender=Camera)
def mirror_camera_softdelete_to_variants(sender, instance: Camera, **kwargs):
    Camera.objects.filter(brand=instance.brand, name=instance.name).exclude(pk=instance.pk).delete()


@receiver(post_softdelete, sender=Sensor)
@receiver(post_softdelete, sender=Camera)
@receiver(post_softdelete, sender=Telescope)
@receiver(post_softdelete, sender=Mount)
@receiver(post_softdelete, sender=Filter)
@receiver(post_softdelete, sender=Accessory)
@receiver(post_softdelete, sender=Software)
def rename_equipment_item_after_deletion(sender, instance, **kwargs):
    if '[DELETED] ' not in instance.name:
        instance.name = f'[DELETED] ({instance.id}) {instance.name}'
        instance.save(keep_deleted=True)


@receiver(post_softdelete, sender=Sensor)
def remove_sensor_from_cameras_after_deletion(sender, instance, **kwargs):
    Camera.objects.filter(sensor=instance).update(sensor=None)

@receiver(post_softdelete, sender=Camera)
def remove_camera_from_presets_after_deletion(sender, instance, **kwargs):
    preset: EquipmentPreset

    for preset in EquipmentPreset.objects.filter(imaging_cameras=instance).iterator():
        preset.imaging_cameras.remove(instance)

    for preset in EquipmentPreset.objects.filter(guiding_cameras=instance).iterator():
        preset.guiding_cameras.remove(instance)


@receiver(post_softdelete, sender=Telescope)
def remove_telescope_from_presets_after_deletion(sender, instance, **kwargs):
    preset: EquipmentPreset

    for preset in EquipmentPreset.objects.filter(imaging_telescopes=instance).iterator():
        preset.imaging_telescopes.remove(instance)

    for preset in EquipmentPreset.objects.filter(guiding_telescopes=instance).iterator():
        preset.guiding_telescopes.remove(instance)


@receiver(post_softdelete, sender=Mount)
def remove_mount_from_presets_after_deletion(sender, instance, **kwargs):
    preset: EquipmentPreset

    for preset in EquipmentPreset.objects.filter(mounts=instance).iterator():
        preset.mounts.remove(instance)


@receiver(post_softdelete, sender=Filter)
def remove_filter_from_presets_after_deletion(sender, instance, **kwargs):
    preset: EquipmentPreset

    for preset in EquipmentPreset.objects.filter(filters=instance).iterator():
        preset.filters.remove(instance)


@receiver(post_softdelete, sender=Accessory)
def remove_accessory_from_presets_after_deletion(sender, instance, **kwargs):
    preset: EquipmentPreset

    for preset in EquipmentPreset.objects.filter(accessories=instance).iterator():
        preset.accessories.remove(instance)


@receiver(post_softdelete, sender=Software)
def remove_software_from_presets_after_deletion(sender, instance, **kwargs):
    preset: EquipmentPreset

    for preset in EquipmentPreset.objects.filter(software=instance).iterator():
        preset.software.remove(instance)


@receiver(post_save, sender=SensorEditProposal)
@receiver(post_save, sender=CameraEditProposal)
@receiver(post_save, sender=TelescopeEditProposal)
@receiver(post_save, sender=MountEditProposal)
@receiver(post_save, sender=FilterEditProposal)
@receiver(post_save, sender=AccessoryEditProposal)
@receiver(post_save, sender=SoftwareEditProposal)
def send_edit_proposal_created_notification(sender, instance, created, **kwargs):
    if created and instance.edit_proposal_target.created_by:
        target = instance.edit_proposal_target
        owner = instance.edit_proposal_target.created_by
        user = instance.edit_proposal_by

        recipients = []

        if owner != user:
            recipients.append(owner)

        previous_proposals = User.objects.filter(
            **{
                f'astrobin_apps_equipment_{instance.__class__.__name__.lower()}_edit_proposals__'
                f'edit_proposal_target': target
            }
        )
        previous_proposals_reviewed = User.objects.filter(
            **{
                f'astrobin_apps_equipment_{instance.__class__.__name__.lower()}_edit_proposals_reviewed__'
                f'edit_proposal_target': target
            }
        )
        commenters = User.objects.filter(
            pk__in=NestedComment.objects.filter(
                content_type=ContentType.objects.get_for_model(instance.__class__),
                object_id__in=instance.__class__.objects.filter(edit_proposal_target=target)
            ).values_list('author', flat=True)
        )
        recipients.extend(list(previous_proposals))
        recipients.extend(list(previous_proposals_reviewed))
        recipients.extend(list(commenters))
        recipients = list(set(recipients))
        if user in recipients:
            recipients.remove(user)

        if len(recipients) > 0 and user:
            push_notification(
                recipients,
                user,
                'equipment-edit-proposal-created',
                {
                    'user': user.userprofile.get_display_name(),
                    'user_url': build_notification_url(
                        settings.BASE_URL + reverse('user_page', args=(user.username,))
                    ),
                    'item': f'{target.brand.name if target.brand else _("(DIY)")} {target.name}',
                    'item_url': build_notification_url(
                        AppRedirectionService.redirect(
                            f'/equipment'
                            f'/explorer'
                            f'/{target.item_type}/{target.pk}'
                            f'/{target.slug}'
                        )
                    ),
                    'unapproved': target.reviewer_decision is None,
                    'edit_proposal_url': build_notification_url(
                        AppRedirectionService.redirect(
                            f'/equipment'
                            f'/explorer'
                            f'/{target.item_type}/{target.pk}'
                            f'/{target.slug}'
                            f'/edit-proposals'
                            f'/{instance.pk}/'
                        )
                    ),
                }
            )


@receiver(post_softdelete, sender=EquipmentBrand)
def rename_equipment_brand_after_deletion(sender, instance: EquipmentBrand, **kwargs):
    if '[DELETED] ' not in instance.name:
        instance.name = f'[DELETED] {instance.name} ({instance.pk}'
        instance.save(keep_deleted=True)


@receiver(post_softdelete, sender=EquipmentPreset)
def rename_equipment_preset_after_deletion(sender, instance: EquipmentPreset, **kwargs):
    if '[DELETED] ' not in instance.name:
        instance.name = f'[DELETED] {instance.name} ({instance.pk}'
        instance.save(keep_deleted=True)


@receiver(post_save, sender=Sensor)
@receiver(post_save, sender=Camera)
@receiver(post_save, sender=Telescope)
@receiver(post_save, sender=Mount)
@receiver(post_save, sender=Filter)
@receiver(post_save, sender=Accessory)
@receiver(post_save, sender=Software)
def send_equipment_item_requires_moderation_notification(sender, instance, created: bool, **kwargs):
    if not created:
        return

    if instance.brand is None:
        return

    if (
            instance.klass == EquipmentItemKlass.CAMERA and
            instance.type == CameraType.DSLR_MIRRORLESS and
            (instance.modified or instance.cooled)
    ):
        return

    if instance.reviewer_decision is not None:
        return

    url: str = build_notification_url(instance.get_absolute_url())
    parsed = urlparse(url)
    url_dict = dict(parse_qsl(parsed.query))
    url_dict.update({'request-review': 'true'})
    new_query = urlencode(url_dict)
    parsed = parsed._replace(query=new_query)
    url = urlunparse(parsed)

    if instance.assignee:
        recipients = [instance.assignee] if instance.assignee != instance.created_by else []
    else:
        recipients = User.objects.filter(groups__name=GroupName.EQUIPMENT_MODERATORS).exclude(pk=instance.created_by.pk)
    push_notification(
        recipients,
        None,
        'equipment-item-requires-moderation',
        {
            'user': instance.created_by.userprofile.get_display_name(),
            'user_url': build_notification_url(
                settings.BASE_URL + reverse('user_page', args=(instance.created_by.username,))
            ),
            'item': instance,
            'url': url
        }
    )


@receiver(pre_save, sender=Sensor)
def set_search_friendly_name_for_sensor(sender, instance, **kwargs):
    search_friendly_name = ""

    if instance.brand:
        search_friendly_name += f' {instance.brand.name}'

    search_friendly_name += f' {" ".join(UtilsService.split_text_alphanumerically(instance.name))}'

    instance.search_friendly_name = search_friendly_name.strip()


@receiver(pre_save, sender=Camera)
def set_search_friendly_name_for_camera(sender, instance, **kwargs):
    search_friendly_name = ""

    if instance.brand:
        search_friendly_name += f' {instance.brand.name}'

    search_friendly_name += f' {" ".join(UtilsService.split_text_alphanumerically(instance.name))}'

    if instance.sensor and instance.sensor.color_or_mono == 'C':
        search_friendly_name += f' color'

    if instance.sensor and instance.sensor.color_or_mono == 'M':
        search_friendly_name += f' mono'

    instance.search_friendly_name = search_friendly_name.strip()


@receiver(pre_save, sender=Telescope)
def set_search_friendly_name_for_telescope(sender, instance, **kwargs):
    search_friendly_name = ""

    if instance.brand:
        search_friendly_name += f' {instance.brand.name}'

    search_friendly_name += f' {" ".join(UtilsService.split_text_alphanumerically(instance.name))}'

    if instance.aperture:
        search_friendly_name += f' {instance.aperture} mm'

        if instance.aperture in range(140, 160):
            search_friendly_name += ' 6"'
        elif instance.aperture in range(190, 210):
            search_friendly_name += ' 8"'
        elif instance.aperture in range(240, 260):
            search_friendly_name += ' 10"'
        elif instance.aperture in range(290, 310):
            search_friendly_name += ' 12"'
        elif instance.aperture in range(340, 360):
            search_friendly_name += ' 14"'
        elif instance.aperture in range(390, 410):
            search_friendly_name += ' 16"'

    instance.search_friendly_name = search_friendly_name.strip()


@receiver(pre_save, sender=Mount)
def set_search_friendly_name_for_mount(sender, instance, **kwargs):
    search_friendly_name = ""

    if instance.brand:
        search_friendly_name += f' {instance.brand.name}'

    search_friendly_name += f' {" ".join(UtilsService.split_text_alphanumerically(instance.name))}'

    instance.search_friendly_name = search_friendly_name.strip()


@receiver(pre_save, sender=Filter)
def set_search_friendly_name_for_filter(sender, instance, **kwargs):
    search_friendly_name = ""

    if instance.brand:
        search_friendly_name += f' {instance.brand.name}'

    search_friendly_name += f' {" ".join(UtilsService.split_text_alphanumerically(instance.name))}'

    if instance.bandwidth:
        search_friendly_name += f' {instance.bandwidth} nm'

    instance.search_friendly_name = search_friendly_name.strip()


@receiver(pre_save, sender=Accessory)
def set_search_friendly_name_for_accessory(sender, instance, **kwargs):
    search_friendly_name = ""

    if instance.brand:
        search_friendly_name += f' {instance.brand.name}'

    search_friendly_name += f' {" ".join(UtilsService.split_text_alphanumerically(instance.name))}'

    if (
            "off" in search_friendly_name.lower() and
            "axis" in search_friendly_name.lower() and
            "oag" not in search_friendly_name.lower()
    ):
        search_friendly_name += ' oag'

    if (
        "oag" in search_friendly_name.lower() and
        "axis" not in search_friendly_name.lower()
    ):
        search_friendly_name += ' off axis guider'

    instance.search_friendly_name = search_friendly_name.strip()


@receiver(pre_save, sender=Software)
def set_search_friendly_name_for_software(sender, instance, **kwargs):
    search_friendly_name = ""

    if instance.brand:
        search_friendly_name += f' {instance.brand.name}'

    search_friendly_name += f' {" ".join(UtilsService.split_text_alphanumerically(instance.name))}'

    instance.search_friendly_name = search_friendly_name.strip()


@receiver(pre_save, sender=Sensor)
@receiver(pre_save, sender=Camera)
@receiver(pre_save, sender=Telescope)
@receiver(pre_save, sender=Mount)
@receiver(pre_save, sender=Filter)
@receiver(pre_save, sender=Accessory)
@receiver(pre_save, sender=Software)
def create_equipment_item_forum(sender, instance: EquipmentItem, **kwargs):
    if not instance.brand:
        return

    if instance.reviewer_decision != EquipmentItemReviewerDecision.APPROVED:
        return

    if instance.forum:
        return

    category, created = Category.objects.get_or_create(
        name='Equipment forums',
        slug='equipment-forums',
    )

    instance.forum, created = Forum.objects.get_or_create(
        category=category,
        name=f'{instance}',
    )
