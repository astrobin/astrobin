from annoying.functions import get_object_or_None
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import pre_save, post_migrate, post_save
from django.dispatch import receiver
from django.urls import reverse
from notification import models as notification

from astrobin_apps_equipment.models import Camera, CameraEditProposal
from astrobin_apps_equipment.models.sensor_edit_proposal import SensorEditProposal
from astrobin_apps_equipment.models.telescope_edit_proposal import TelescopeEditProposal
from astrobin_apps_equipment.notice_types import EQUIPMENT_NOTICE_TYPES
from astrobin_apps_notifications.utils import push_notification, build_notification_url
from common.services import AppRedirectionService
from nested_comments.models import NestedComment


@receiver(post_migrate, sender=apps.get_app_config('astrobin'))
def create_notice_types(sender, **kwargs):
    for notice_type in EQUIPMENT_NOTICE_TYPES:
        notification.create_notice_type(notice_type[0], notice_type[1], notice_type[2], default=notice_type[3])


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


# TODO: complete
@receiver(post_save, sender=SensorEditProposal)
@receiver(post_save, sender=CameraEditProposal)
@receiver(post_save, sender=TelescopeEditProposal)
def send_edit_proposal_created_notification(sender, instance, created, **kwargs):
    if created and instance.edit_proposal_target.created_by:
        target = instance.edit_proposal_target
        owner = instance.edit_proposal_target.created_by
        user = instance.edit_proposal_by

        recipients = []

        if owner != user:
            recipients.append(owner)

        previous_proposals = User.objects.filter(**{
            f'astrobin_apps_equipment_{instance.__class__.__name__.lower()}_edit_proposals__'
            f'edit_proposal_target': target
        })
        previous_proposals_reviewed = User.objects.filter(**{
            f'astrobin_apps_equipment_{instance.__class__.__name__.lower()}_edit_proposals_reviewed__'
            f'edit_proposal_target': target
        })
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
        recipients.remove(user)

        if len(recipients) > 0:
            push_notification(
                recipients,
                user,
                'equipment-edit-proposal-created',
                {
                    'user': user.userprofile.get_display_name(),
                    'user_url': build_notification_url(
                        settings.BASE_URL + reverse('user_page', args=(user.username,))),
                    'item': f'{target.brand.name} {target.name}',
                    'item_url': build_notification_url(
                        AppRedirectionService.redirect(
                            f'/equipment'
                            f'/explorer'
                            f'/{target.type}/{target.pk}'
                            f'/{target.slug}'
                        )
                    ),
                    'edit_proposal_url': build_notification_url(
                        AppRedirectionService.redirect(
                            f'/equipment'
                            f'/explorer'
                            f'/{target.type}/{target.pk}'
                            f'/{target.slug}'
                            f'/edit-proposals'
                            f'/{instance.pk}/'
                        )
                    ),
                }
            )
