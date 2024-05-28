from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from annoying.functions import get_object_or_None
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.signals import post_delete, post_migrate, post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from notification import models as notification
from pybb.models import Category, Forum, Topic
from safedelete.signals import post_softdelete

from astrobin.services.utils_service import UtilsService
from astrobin_apps_equipment.models import (
    Accessory, Camera, CameraEditProposal, EquipmentBrand, EquipmentItem, EquipmentItemMarketplaceListing,
    EquipmentItemMarketplaceListingLineItem, EquipmentItemMarketplaceMasterOffer,
    EquipmentItemMarketplaceOffer,
    EquipmentPreset, Filter, Mount, Sensor,
    Software, Telescope,
)
from astrobin_apps_equipment.models.accessory_edit_proposal import AccessoryEditProposal
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_equipment.models.equipment_item import EquipmentItemReviewerDecision
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.models.equipment_item_marketplace_offer import EquipmentItemMarketplaceOfferStatus
from astrobin_apps_equipment.models.filter_edit_proposal import FilterEditProposal
from astrobin_apps_equipment.models.mount_edit_proposal import MountEditProposal
from astrobin_apps_equipment.models.sensor_base_model import ColorOrMono
from astrobin_apps_equipment.models.sensor_edit_proposal import SensorEditProposal
from astrobin_apps_equipment.models.software_edit_proposal import SoftwareEditProposal
from astrobin_apps_equipment.models.telescope_edit_proposal import TelescopeEditProposal
from astrobin_apps_equipment.notice_types import EQUIPMENT_NOTICE_TYPES
from astrobin_apps_equipment.tasks import send_offer_notifications
from astrobin_apps_notifications.utils import build_notification_url, push_notification
from astrobin_apps_users.services import UserService
from common.constants import GroupName
from common.services import AppRedirectionService
from common.services.caching_service import CachingService
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
        klass=instance.klass,
        created_by=instance.created_by,
        brand=instance.brand,
        name=instance.name,
        website=instance.website,
        group=instance.group,
        image=instance.image,
        type=instance.type,
        sensor=instance.sensor,
        cooled=False,
        max_cooling=instance.max_cooling,
        back_focus=instance.back_focus,
        reviewed_by=instance.reviewed_by,
        reviewed_timestamp=instance.reviewed_timestamp,
        reviewer_decision=instance.reviewer_decision,

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
    if instance.variant_of is None:
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

    if instance.sensor and instance.sensor.color_or_mono == ColorOrMono.COLOR.value:
        search_friendly_name += f' color'

    if instance.sensor and instance.sensor.color_or_mono == ColorOrMono.MONO.value:
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
def create_or_delete_equipment_item_forum(sender, instance: EquipmentItem, **kwargs):
    if not instance.brand:
        return

    category, created = Category.objects.get_or_create(
        name='Equipment forums',
        slug='equipment-forums',
    )

    if instance.reviewer_decision == EquipmentItemReviewerDecision.APPROVED:
        if not instance.forum:
            instance.forum, created = Forum.objects.get_or_create(
                category=category,
                name=f'{instance}',
            )
    else:
        if instance.forum is not None:
            if instance.reviewer_rejection_duplicate_of:
                DuplicateModelClass = {
                    EquipmentItemKlass.SENSOR: Sensor,
                    EquipmentItemKlass.TELESCOPE: Telescope,
                    EquipmentItemKlass.CAMERA: Camera,
                    EquipmentItemKlass.MOUNT: Mount,
                    EquipmentItemKlass.FILTER: Filter,
                    EquipmentItemKlass.ACCESSORY: Accessory,
                    EquipmentItemKlass.SOFTWARE: Software
                }.get(instance.reviewer_rejection_duplicate_of_klass)

                ModelClass = type(instance)

                try:
                    duplicate_of = DuplicateModelClass.objects.get(pk=instance.reviewer_rejection_duplicate_of)
                    Topic.objects.filter(forum=instance.forum).update(forum=duplicate_of.forum)
                except ModelClass.DoesNotExist:
                    instance.forum.delete()
                    instance.forum = None
            else:
                instance.forum.delete()
                instance.forum = None


@receiver(pre_save, sender=EquipmentItemMarketplaceOffer)
def create_and_sync_master_offer(sender, instance: EquipmentItemMarketplaceOffer, **kwargs):
    with transaction.atomic():
        master_offer, _ = EquipmentItemMarketplaceMasterOffer.objects.get_or_create(
            listing=instance.line_item.listing,
            user=instance.user,
        )

    if master_offer.status != instance.status:
        master_offer.status = instance.status
        master_offer.save()

    instance.master_offer = master_offer


@receiver(post_save, sender=EquipmentItemMarketplaceOffer)
def send_offer_created_notifications(sender, instance: EquipmentItemMarketplaceOffer, created: bool, **kwargs):
    if created:
        send_offer_notifications.apply_async(
            args=[
                instance.listing.pk,
                instance.user.pk,
                instance.pk,
                [instance.listing.user.pk],
                instance.user.pk,
                'marketplace-offer-created',
            ], countdown=10
        )


@receiver(post_delete, sender=EquipmentItemMarketplaceOffer)
def delete_master_offer(sender, instance: EquipmentItemMarketplaceOffer, **kwargs):
    master_offer = get_object_or_None(
        EquipmentItemMarketplaceMasterOffer,
        listing=instance.listing,
        user=instance.user
    )

    if master_offer and master_offer.offers.count() == 0:
        master_offer.status = instance.status
        master_offer.delete()


@receiver(post_delete, sender=EquipmentItemMarketplaceMasterOffer)
def send_offer_retracted_or_rejected_notification(sender, instance: EquipmentItemMarketplaceMasterOffer, **kwargs):
    if instance.status == EquipmentItemMarketplaceOfferStatus.REJECTED.value:
        # This offer is being deleted because it was rejected. If an offer is simpy retracted, the status would be
        # PENDING.
        send_offer_notifications.apply_async(
            args=[
                instance.listing.pk,
                instance.user.pk,
                None,
                [instance.listing.user.pk],
                instance.user.pk,
                'marketplace-offer-rejected-by-seller',
            ], countdown=10
        )
    else:
        # This offer must've been retracted by the user.
        send_offer_notifications.apply_async(
            args=[
                instance.listing.pk,
                instance.user.pk,
                None,
                [instance.listing.user.pk],
                instance.user.pk,
                'marketplace-offer-retracted',
            ], countdown=10
        )


@receiver(pre_save, sender=EquipmentItemMarketplaceOffer)
def prepare_offer_updated_notifications(sender, instance: EquipmentItemMarketplaceOffer, **kwargs):
    before = get_object_or_None(EquipmentItemMarketplaceOffer, pk=instance.pk)
    after = instance

    if before is not None and before.amount != after.amount:
        instance.pre_save_amount_changed = True


@receiver(post_save, sender=EquipmentItemMarketplaceOffer)
def send_offer_updated_notifications(sender, instance: EquipmentItemMarketplaceOffer, **kwargs):
    if instance.pre_save_amount_changed:
        send_offer_notifications.apply_async(
            args=[
                instance.listing.pk,
                instance.user.pk,
                instance.pk,
                [instance.line_item.user.pk],
                instance.user.pk,
                'marketplace-offer-updated',
            ], countdown=10
        )

        del instance.pre_save_amount_changed


@receiver(pre_save, sender=EquipmentItemMarketplaceMasterOffer)
def send_offer_accepted_notifications(sender, instance: EquipmentItemMarketplaceMasterOffer, **kwargs):
    before = get_object_or_None(EquipmentItemMarketplaceMasterOffer, pk=instance.pk)
    after = instance

    if (
            before is not None and
            before.status == EquipmentItemMarketplaceOfferStatus.PENDING.value and
            after.status == EquipmentItemMarketplaceOfferStatus.ACCEPTED.value
    ):
        send_offer_notifications.apply_async(
            args=[
                instance.listing.pk,
                instance.user.pk,
                None,
                [instance.user.pk],
                instance.listing.user.pk,
                'marketplace-offer-accepted-by-seller',
            ], countdown=10
        )

        send_offer_notifications.apply_async(
            args=[
                instance.listing.pk,
                instance.user.pk,
                None,
                [instance.listing.user.pk],
                None,
                'marketplace-offer-accepted-by-you',
            ], countdown=10
        )


@receiver(pre_save, sender=EquipmentItemMarketplaceListing)
def marketplace_listing_pre_save(sender, instance: EquipmentItemMarketplaceListing, **kwargs):
    if instance.pk:
        pre_save_instance = EquipmentItemMarketplaceListing.objects.get(pk=instance.pk)

        # The item is being approved.
        if (
                pre_save_instance.approved is None and
                pre_save_instance.first_approved is None and
                instance.approved is not None
        ):
            instance.pre_save_approved = True

        # The item is being approved (not for the first time)
        if (
                pre_save_instance.approved is None and
                pre_save_instance.first_approved is not None and
                instance.approved is not None
        ):
            instance.pre_save_approved_again = True

        # try to get user who is updating the listing
        caching_service = CachingService()
        caching_key = f'user_updating_marketplace_instance_{instance.pk}'
        user = caching_service.get_from_request_cache(caching_key)
        is_moderator = UserService(user).is_in_group(GroupName.MARKETPLACE_MODERATORS) if user else False
        caching_service.delete_from_request_cache(caching_key)

        # The item is being updated while approved
        if pre_save_instance.approved and not is_moderator:
            instance.approved = None
            instance.approved_by = None


@receiver(post_save, sender=EquipmentItemMarketplaceListing)
def marketplace_listing_post_save(sender, instance: EquipmentItemMarketplaceListing, created: bool, **kwargs):
    if not created:
        if instance.pre_save_approved or instance.pre_save_approved_again:
            push_notification(
                [instance.user],
                None,
                'marketplace-listing-approved',
                {
                    'user': instance.approved_by.userprofile.get_display_name() if instance.approved_by else 'AstroBin',
                    'listing': instance,
                    'listing_url': build_notification_url(instance.get_absolute_url())
                }
            )

        if instance.pre_save_approved:
            seller_followers = list(User.objects.filter(
                toggleproperty__content_type=ContentType.objects.get_for_model(instance.user),
                toggleproperty__object_id=instance.user.id,
                toggleproperty__property_type="follow",
                joined_group_set__name=GroupName.BETA_TESTERS
            ).distinct())

            if len(seller_followers):
                push_notification(
                    seller_followers,
                    instance.user,
                    'marketplace-listing-by-user-you-follow',
                    {
                        'seller_display_name': instance.user.userprofile.get_display_name(),
                        'listing': instance,
                        'listing_url': build_notification_url(instance.get_absolute_url())
                    }
                )

            for line_item in instance.line_items.filter(sold__isnull=True):
                equipment_followers = list(User.objects.filter(
                    toggleproperty__content_type=line_item.item_content_type,
                    toggleproperty__object_id=line_item.item_object_id,
                    toggleproperty__property_type="follow",
                    joined_group_set__name=GroupName.BETA_TESTERS
                ).distinct())

                if len(equipment_followers):
                    push_notification(
                        equipment_followers,
                        instance.user,
                        'marketplace-listing-for-item-you-follow',
                        {
                            'seller_display_name': instance.user.userprofile.get_display_name(),
                            'listing': instance,
                            'listing_url': build_notification_url(instance.get_absolute_url()),
                            'line_item': line_item,
                        }
                    )
        else:
            # The item is being updated and not merely approved.

            users_with_offers = User.objects.filter(
                equipment_item_marketplace_listings_offers__listing=instance
            ).distinct()

            followers = User.objects.filter(
                toggleproperty__content_type=ContentType.objects.get_for_model(instance),
                toggleproperty__object_id=instance.id,
                toggleproperty__property_type="follow"
            ).distinct()

            recipients = list(set(list(users_with_offers) + list(followers)))

            if len(recipients):
                push_notification(
                    recipients,
                    instance.user,
                    'marketplace-listing-updated',
                    {
                        'seller_display_name': instance.user.userprofile.get_display_name(),
                        'listing': instance,
                        'listing_url': build_notification_url(instance.get_absolute_url())
                    }
                )


@receiver(post_softdelete, sender=EquipmentItemMarketplaceListing)
def marketplace_listing_post_softdelete(sender, instance: EquipmentItemMarketplaceListing, **kwargs):
    users_with_offers = User.objects.filter(
        equipment_item_marketplace_listings_offers__listing=instance
    ).distinct()

    followers = User.objects.filter(
        toggleproperty__content_type=ContentType.objects.get_for_model(instance),
        toggleproperty__object_id=instance.id,
        toggleproperty__property_type="follow"
    ).distinct()

    recipients = list(set(list(users_with_offers) + list(followers)))

    if len(recipients):
        push_notification(
            recipients,
            instance.user,
            'marketplace-listing-deleted',
            {
                'seller_display_name': instance.user.userprofile.get_display_name(),
                'listing': instance,
            }
        )


@receiver(pre_save, sender=EquipmentItemMarketplaceListingLineItem)
def marketplace_listing_line_item_pre_save(sender, instance: EquipmentItemMarketplaceListingLineItem, **kwargs):
    if instance.pk:
        pre_save_instance = EquipmentItemMarketplaceListingLineItem.objects.get(pk=instance.pk)
        if pre_save_instance.sold is None and instance.sold is not None:
            instance.pre_save_sold = True


@receiver(post_save, sender=EquipmentItemMarketplaceListingLineItem)
def marketplace_listing_line_item_post_save(sender, instance: EquipmentItemMarketplaceListingLineItem, **kwargs):
    if instance.pre_save_sold:
        users_with_offers = User.objects.filter(
            equipment_item_marketplace_listings_offers__line_item=instance
        )

        if instance.sold_to:
            users_with_offers = users_with_offers.exclude(pk=instance.sold_to.pk)

        users_with_offers = users_with_offers.distinct()

        followers = User.objects.filter(
            toggleproperty__content_type=ContentType.objects.get_for_model(instance.listing),
            toggleproperty__object_id=instance.listing.id,
            toggleproperty__property_type="follow"
        )

        if instance.sold_to:
            followers = followers.exclude(pk=instance.sold_to.pk)

        followers = followers.distinct()

        recipients = list(set(list(users_with_offers) + list(followers)))

        if len(recipients):
            push_notification(
                recipients,
                instance.listing.user,
                'marketplace-listing-line-item-sold',
                {
                    'seller_display_name': instance.listing.user.userprofile.get_display_name(),
                    'buyer_display_name': instance.sold_to.userprofile.get_display_name()
                    if instance.sold_to
                    else _('Unspecified'),
                    'listing': instance.listing,
                    'line_item': instance,
                    'listing_url': build_notification_url(instance.listing.get_absolute_url())
                }
            )

        del instance.pre_save_sold
