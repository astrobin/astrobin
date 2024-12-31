import datetime
import logging
import re
from itertools import chain
from typing import List, Set

import stripe
from actstream.actions import follow, unfollow
from annoying.functions import get_object_or_None
from avatar.models import Avatar
from avatar.signals import avatar_deleted, avatar_updated
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import Group as DjangoGroup, User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import IntegrityError, InternalError, transaction
from django.db.models import Q
from django.db.models.signals import (m2m_changed, post_delete, post_save, pre_delete, pre_save)
from django.dispatch import receiver
from django.urls import reverse as reverse_url
from django.utils import timezone
from django.utils.translation import gettext, override
from persistent_messages.models import Message
from pybb.models import Forum, Post, Topic, TopicReadTracker
from pybb.permissions import perms
from pybb.util import get_pybb_profile
from rest_framework.authtoken.models import Token
from safedelete import HARD_DELETE
from safedelete.config import FIELD_NAME as DELETED_FIELD_NAME
from safedelete.signals import post_softdelete, post_undelete
from stripe.error import StripeError
from subscription.models import Subscription, Transaction, UserSubscription
from subscription.signals import paid, signed_up, unsubscribed
from subscription.utils import extend_date_by
from two_factor.signals import user_verified

from astrobin.tasks import (
    compute_contribution_index, compute_image_index, encode_video_file, generate_video_preview, invalidate_cdn_caches,
    process_camera_rename_proposal,
)
from astrobin_apps_equipment.models import EquipmentBrand, EquipmentItem, EquipmentPreset
from astrobin_apps_equipment.services import EquipmentItemService
from astrobin_apps_equipment.tasks import (
    approve_migration_strategy, update_equipment_preset_image_count,
    update_equipment_preset_total_integration,
)
from astrobin_apps_forum.services import ForumService
from astrobin_apps_forum.tasks import notify_equipment_users
from astrobin_apps_groups.models import Group
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.models import (
    IotdDismissedImage, IotdSubmission, IotdVote, TopPickArchive,
    TopPickNominationsArchive,
)
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_iotd.templatetags.astrobin_apps_iotd_tags import humanize_may_not_submit_to_iotd_tp_process_reason
from astrobin_apps_iotd.types.may_not_submit_to_iotd_tp_reason import MayNotSubmitToIotdTpReason
from astrobin_apps_notifications.services import NotificationsService
from astrobin_apps_notifications.tasks import (
    push_notification_for_new_image, push_notification_for_new_image_revision,
    push_notification_task,
)
from astrobin_apps_notifications.utils import (
    build_notification_url, clear_notifications_template_cache,
    push_notification,
)
from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.solver import Solver
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import (
    is_any_paid_subscription, is_any_ultimate, is_free, is_lite, is_lite_2020, is_premium, is_premium_2020,
)
from astrobin_apps_users.services import MailingListService, UserService
from common.constants import GroupName
from common.models import ABUSE_REPORT_DECISION_OVERRULED, AbuseReport
from common.services import AppRedirectionService, DateTimeService, SearchIndexUpdateService
from common.services.mentions_service import MentionsService
from common.services.moderation_service import ModerationService
from common.utils import batch
from nested_comments.models import NestedComment
from nested_comments.services.comment_notifications_service import CommentNotificationsService
from toggleproperties.models import ToggleProperty
from .enums.moderator_decision import ModeratorDecision
from .models import (
    Accessory, Camera, CameraRenameProposal, Collection, DeepSky_Acquisition, Filter, FocalReducer, Gear,
    GearMigrationStrategy, Image,
    ImageEquipmentLog, ImageRevision,
    Mount,
    Software, Telescope,
    UserProfile,
)
from .search_indexes import ImageIndex, UserIndex
from .stories import (
    ACTSTREAM_VERB_BOOKMARKED_IMAGE,
    ACTSTREAM_VERB_CREATED_PUBLIC_GROUP,
    ACTSTREAM_VERB_JOINED_GROUP,
    ACTSTREAM_VERB_LIKED_IMAGE,
    ACTSTREAM_VERB_UPLOADED_IMAGE,
    ACTSTREAM_VERB_UPLOADED_REVISION,
    add_story,
)
from .utils import get_client_country_code

log = logging.getLogger(__name__)


def image_pre_save(sender, instance, **kwargs):
    if instance.uploader_in_progress:
        return

    if not instance.pk and not instance.is_wip:
        instance.published = datetime.datetime.now()

    if instance.square_cropping in (None, ''):
        instance.square_cropping = ImageService(instance).get_default_cropping() or ""

    try:
        image = sender.objects_including_wip.get(pk=instance.pk)
    except sender.DoesNotExist:
        # Image is being created.

        last_image: Image = Image.objects_including_wip.filter(user=instance.user).order_by('-pk').first()
        if last_image:
            instance.watermark = last_image.watermark
            instance.watermark_text = last_image.watermark_text
            instance.watermark_position = last_image.watermark_position
            instance.watermark_size = last_image.watermark_size
            instance.watermark_opacity = last_image.watermark_opacity

        image_index = instance.user.userprofile.get_scores()['user_scores_index'] or 0
        if not ModerationService.auto_enqueue_for_moderation(instance.user) and (
                image_index >= 1.00 or
                is_any_paid_subscription(PremiumService(instance.user).get_valid_usersubscription()) or
                ModerationService.auto_approve(instance.user)
        ):
            instance.moderated_when = datetime.date.today()
            instance.moderator_decision = ModeratorDecision.APPROVED
    else:
        if (
                image.moderator_decision != ModeratorDecision.APPROVED and
                instance.moderator_decision == ModeratorDecision.APPROVED
        ):
            # This image is being approved
            if not instance.is_wip and not image.skip_activity_stream:
                add_story(instance.user, verb=ACTSTREAM_VERB_UPLOADED_IMAGE, action_object=instance)

        if not instance.is_wip and not instance.published:
            # This image is being published
            instance.published = datetime.datetime.now()

        previous_mentions = MentionsService.get_mentions(image.description_bbcode)
        current_mentions = MentionsService.get_mentions(instance.description_bbcode)
        mentions = [item for item in current_mentions if item not in previous_mentions]
        cache.set("image.%d.image_pre_save_mentions" % instance.pk, mentions, 2)

        if (
                instance.watermark_text != image.watermark_text or
                instance.watermark != image.watermark or
                instance.watermark_position != image.watermark_position or
                instance.watermark_size != image.watermark_size or
                instance.watermark_opacity != image.watermark_opacity
        ):
            ImageService(image).invalidate_all_thumbnails()


pre_save.connect(image_pre_save, sender=Image)


def image_pre_save_invalidate_thumbnails(sender, instance: Image, **kwargs):
    try:
        image_before_saving: Image = sender.objects_including_wip.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    if image_before_saving.square_cropping not in (None, '', '0,0,0,0') and \
            image_before_saving.square_cropping != instance.square_cropping:
        instance.thumbnail_invalidate()


pre_save.connect(image_pre_save_invalidate_thumbnails, sender=Image)


@receiver(post_save, sender=Image)
def image_post_save(sender, instance: Image, created: bool, **kwargs):
    if kwargs.get('update_fields', None):
        return

    if getattr(instance, DELETED_FIELD_NAME, None):
        return

    content_type = ContentType.objects.get_for_model(Image)

    if created:
        instance.user.userprofile.premium_counter += 1
        instance.user.userprofile.save(keep_deleted=True)

        if not instance.is_wip:
            if not instance.skip_notifications:
                push_notification_for_new_image.apply_async(args=(instance.pk,))
            if instance.moderator_decision == ModeratorDecision.APPROVED and not instance.skip_activity_stream:
                add_story(instance.user, verb=ACTSTREAM_VERB_UPLOADED_IMAGE, action_object=instance)

        if Image.all_objects.filter(user=instance.user).count() == 1:
            push_notification(
                [instance.user], None, 'congratulations_for_your_first_image', {
                    'BASE_URL': settings.BASE_URL,
                    'PREMIUM_MAX_IMAGES_FREE': settings.PREMIUM_MAX_IMAGES_FREE,
                    'url': reverse_url('image_detail', args=(instance.get_id(),))
                }
            )

        mentions = MentionsService.get_mentions(instance.description_bbcode)
    else:
        mentions = cache.get("image.%d.image_pre_save_mentions" % instance.pk, [])

    for username in mentions:
        user = get_object_or_None(User, username=username)
        if not user:
            try:
                profile = get_object_or_None(UserProfile, real_name=username)
                if profile:
                    user = profile.user
            except MultipleObjectsReturned:
                user = None
        if user and user != instance.user:
            thumb = instance.thumbnail_raw('gallery', None, sync=True)
            push_notification(
                [user], instance.user, 'new_image_description_mention',
                {
                    'preheader': instance.title,
                    'image': instance,
                    'image_thumbnail': thumb.url if thumb else None,
                    'url': build_notification_url(settings.BASE_URL + instance.get_absolute_url(), instance.user),
                    'user': instance.user.userprofile.get_display_name(),
                    'user_url': settings.BASE_URL + reverse_url('user_page', kwargs={'username': instance.user}),
                }
            )

    if not instance.uploader_in_progress:
        if instance.video_file.name:
            if not instance.image_file.name:
                ImageService(instance).generate_loading_placeholder()
                generate_video_preview.apply_async(args=(instance.pk, content_type.pk))

            if not instance.encoded_video_file.name:
                log.debug(f'Encoding video file for {instance} in image_post_save signal handler')
                encode_video_file.apply_async(args=(instance.pk, content_type.pk))

        groups = instance.user.joined_group_set.filter(autosubmission=True)
        for group in groups:
            if instance.is_wip:
                group.images.remove(instance)
            else:
                group.images.add(instance)

        if instance.user.userprofile.updated < datetime.datetime.now() - datetime.timedelta(minutes=5):
            instance.user.save()
            try:
                instance.user.userprofile.save(keep_deleted=True)
            except UserProfile.DoesNotExist:
                pass

        if instance.moderator_decision == ModeratorDecision.APPROVED:
            UserService(instance.user).update_image_count()
            for collaborator in instance.collaborators.all():
                UserService(collaborator).update_image_count()

        from astrobin_apps_platesolving.tasks import start_basic_solver
        start_basic_solver.apply_async(args=(instance.pk, content_type.pk), countdown=30)

        UserService(instance.user).clear_gallery_image_list_cache()
        ImageService(instance).clear_badges_cache()

        if instance.user.userprofile.auto_submit_to_iotd_tp_process and not instance.is_wip:
            may, reason = IotdService.submit_to_iotd_tp_process(instance.user, instance)

            if not may and reason in (
                    MayNotSubmitToIotdTpReason.IS_FREE,
                    MayNotSubmitToIotdTpReason.NO_TELESCOPE_OR_CAMERA,
                    MayNotSubmitToIotdTpReason.NO_ACQUISITIONS,
                    MayNotSubmitToIotdTpReason.DID_NOT_AGREE_TO_RULES_AND_GUIDELINES,
            ):
                cache_key = 'image.%d.image_not_submitted_to_iotd_tp' % instance.pk
                if not cache.get(cache_key):
                    cache.set(cache_key, True, 4)
                    thumb = instance.thumbnail_raw('gallery', None, sync=True)
                    push_notification(
                        [instance.user], None, 'image_not_submitted_to_iotd_tp', {
                            'preheader': instance.title,
                            'image': instance,
                            'image_thumbnail': thumb.url if thumb else None,
                            'reason': humanize_may_not_submit_to_iotd_tp_process_reason(reason),
                            'raw_reason': reason,
                        }
                    )

        if instance.user.userprofile.gallery_header_image is None:
            instance.user.userprofile.gallery_header_image = instance.thumbnail('hd', None, sync=True)
            instance.user.userprofile.save(keep_deleted=True)

        for preset in EquipmentPreset.objects.filter(user=instance.user):
            update_equipment_preset_image_count.delay(preset.pk)
            update_equipment_preset_total_integration.delay(preset.pk)


@receiver(post_softdelete, sender=Image)
def image_post_softdelete(sender, instance, **kwargs):
    def decrease_counter(user):
        user.userprofile.premium_counter -= 1
        with transaction.atomic():
            user.userprofile.save(keep_deleted=True)

    ImageIndex().remove_object(instance)
    UserService(instance.user).clear_gallery_image_list_cache()
    ImageService(instance).delete_stories()

    if instance.moderator_decision == ModeratorDecision.APPROVED:
        UserService(instance.user).update_image_count()
        for collaborator in instance.collaborators.all():
            UserService(collaborator).update_image_count()

    if instance.solution:
        cache.delete(f'astrobin_solution_{instance.__class__.__name__}_{instance.pk}')
        try:
            instance.solution.delete()
        except (AttributeError, AssertionError):
            pass

    valid_subscription = PremiumService(instance.user).get_valid_usersubscription()

    try:
        if instance.uploaded > datetime.datetime.now() - relativedelta(hours=24):
            decrease_counter(instance.user)
        elif is_lite(valid_subscription):
            user_subscription = PremiumService(instance.user).get_valid_usersubscription()
            user_subscription_created = user_subscription.expires - relativedelta(years=1)
            dt = instance.uploaded.date() - user_subscription_created
            if dt.days >= 0:
                decrease_counter(instance.user)
        elif is_lite_2020(valid_subscription) or \
                is_premium(valid_subscription) or \
                is_premium_2020(valid_subscription) or \
                is_any_ultimate(valid_subscription):
            decrease_counter(instance.user)
    except IntegrityError:
        # Possibly the user is being deleted
        pass

    instance.collections.clear()


@receiver(pre_delete, sender=Image)
def image_pre_delete(sender, instance: Image, **kwargs):
    if not getattr(instance, DELETED_FIELD_NAME, None):
        try:
            image_post_softdelete(sender, instance, **kwargs)
        except InternalError as e:
            log.error("Error soft deleting image %d: %s" % (instance.pk, str(e)))

    if instance.image_file:
        if instance.image_file.url and getattr(instance, "purge_caches", False):
            invalidate_cdn_caches.delay([instance.image_file.url])
        else:
            if not instance.image_file.url:
                log.debug(f"image_pre_delete: Image {instance.pk} has no image_file.url")
            if not getattr(instance, "purge_caches", False):
                log.debug(f"image_pre_delete: Image {instance.pk} has no purge_caches attribute")
        instance.image_file.delete(save=False)


@receiver(post_delete, sender=Image)
def image_post_delete(sender, instance, **kwargs):
    UserService(instance.user).update_image_count()
    for collaborator in instance.collaborators.all():
        UserService(collaborator).update_image_count()
    NestedComment.objects.filter(
        content_type=ContentType.objects.get_for_model(Image),
        object_id=instance.pk
    ).delete()


@receiver(pre_save, sender=ImageRevision)
def imagerevision_pre_save(sender, instance: ImageRevision, **kwargs):
    if not instance.uploader_in_progress and instance.square_cropping in (None, ''):
        instance.square_cropping = ImageService(instance.image).get_default_cropping(instance.label) or ""

    if instance.pk:
        pre_save_instance = get_object_or_None(ImageRevision.uploads_in_progress, pk=instance.pk)
        if pre_save_instance and not instance.uploader_in_progress:
            cache.set("image_revision.%s.just_completed_upload" % instance.pk, True, 10)

        if not pre_save_instance:
            pre_save_instance = get_object_or_None(ImageRevision, pk=instance.pk)

            if (
                    pre_save_instance and
                    pre_save_instance.square_cropping not in (None, '', '0,0,0,0') and
                    pre_save_instance.square_cropping != instance.square_cropping
            ):
                instance.thumbnail_invalidate()


def imagerevision_post_save(sender, instance: ImageRevision, created: bool, **kwargs):
    if kwargs.get('update_fields', None):
        return

    uploading = instance.uploader_in_progress
    content_type = ContentType.objects.get_for_model(ImageRevision)

    if not uploading:
        if instance.video_file.name:
            if not instance.image_file.name:
                ImageService(instance.image).generate_loading_placeholder(revision_label=instance.label)
                generate_video_preview.apply_async(args=(instance.pk, content_type.pk))

            if not instance.encoded_video_file.name:
                log.debug(f'Encoding video file for {instance} in imagerevision_post_save signal handler')
                encode_video_file.apply_async(args=(instance.pk, content_type.pk))

        if instance.image.submitted_for_iotd_tp_consideration:
            for alias in ('story', 'hd_anonymized', 'hd_anonymized_crop', 'real_anonymized'):
                instance.thumbnail(alias)

        from astrobin_apps_platesolving.tasks import start_basic_solver
        start_basic_solver.apply_async(args=(instance.pk, content_type.pk), countdown=30)

    if instance.image.is_wip:
        return

    skip_notifications = instance.skip_notifications
    skip_activity_stream = instance.skip_activity_stream
    just_completed_upload = cache.get("image_revision.%s.just_completed_upload" % instance.pk)

    UserService(instance.image.user).clear_gallery_image_list_cache()

    if (created and not uploading) or just_completed_upload:
        if not skip_notifications:
            push_notification_for_new_image_revision.apply_async(args=(instance.pk,), countdown=10)
        if not skip_activity_stream:
            add_story(
                instance.image.user,
                verb=ACTSTREAM_VERB_UPLOADED_REVISION,
                action_object=instance,
                target=instance.image,
                like_count=ToggleProperty.objects.toggleproperties_for_object('like', instance.image).count(),
                bookmark_count=ToggleProperty.objects.toggleproperties_for_object('bookmark', instance.image).count(),
                comment_count=NestedComment.objects.filter(
                    content_type=ContentType.objects.get_for_model(Image),
                    object_id=instance.image.pk,
                    deleted=False
                ).count()
            )


post_save.connect(imagerevision_post_save, sender=ImageRevision)


@receiver(post_softdelete, sender=ImageRevision)
def imagerevision_post_softdelete(sender, instance, **kwargs):
    UserService(instance.image.user).clear_gallery_image_list_cache()
    if instance.solution:
        cache.delete(f'astrobin_solution_{instance.__class__.__name__}_{instance.pk}')
        try:
            instance.solution.delete()
        except AttributeError:
            pass

    if instance.is_final:
        instance.image.revisions.filter(pk=instance.pk).update(is_final=False)
        Image.objects_including_wip.filter(pk=instance.image.pk).update(
            is_final=True,
            updated=timezone.now()
        )


@receiver(pre_delete, sender=ImageRevision)
def imagerevision_pre_delete(sender, instance: ImageRevision, **kwargs):
    if not getattr(instance, DELETED_FIELD_NAME, None):
        try:
            imagerevision_post_softdelete(sender, instance, **kwargs)
        except InternalError as e:
            log.error("Error soft deleting image revision %d: %s" % (instance.pk, str(e)))

    if instance.image_file:
        if instance.image_file.url and getattr(instance, "purge_caches", False):
            invalidate_cdn_caches.delay([instance.image_file.url])
        else:
            if not instance.image_file.url:
                log.debug(f"imagerevision_pre_delete: ImageRevision {instance.pk} has no image_file.url")
            if not getattr(instance, "purge_caches", False):
                log.debug(f"imagerevision_pre_delete: ImageRevision {instance.pk} has no purge_caches attribute")
        instance.image_file.delete(save=False)


def nested_comment_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            previous_mentions = MentionsService.get_mentions(sender.objects.get(pk=instance.pk).text)
            current_mentions = MentionsService.get_mentions(instance.text)
            mentions = [item for item in current_mentions if item not in previous_mentions]
        except sender.DoesNotExist:
            mentions = []

        cache.set("user.%d.comment_pre_save_mentions" % instance.author.pk, mentions, 2)
    else:
        insufficient_index = instance.author.userprofile.get_scores()['user_scores_index'] is not None and \
                             instance.author.userprofile.get_scores()['user_scores_index'] < 1.00
        valid_subscription = PremiumService(instance.author).get_valid_usersubscription()
        free_account = is_free(valid_subscription)
        insufficient_previous_approvals = NestedComment.objects.filter(
            Q(author=instance.author) & ~Q(pending_moderation=True)
        ).count() < 3

        is_content_owner = False
        ct = ContentType.objects.get_for_id(instance.content_type_id)
        if ct.model == 'image':
            is_content_owner = instance.author == instance.content_object.user

        if ModerationService.auto_enqueue_for_moderation(instance.author) or \
                insufficient_index and \
                free_account and \
                insufficient_previous_approvals and \
                not is_content_owner and \
                not ModerationService.auto_approve(instance.author):
            instance.pending_moderation = True


pre_save.connect(nested_comment_pre_save, sender=NestedComment)


def nested_comment_post_save(sender, instance, created, **kwargs):
    service = CommentNotificationsService(instance)

    compute_contribution_index.apply_async(args=(instance.author.pk,), countdown=10)

    if created:
        mentions = MentionsService.get_mentions(instance.text)

        if hasattr(instance.content_object, "updated"):
            instance.content_type.model_class().objects.filter(
                pk=instance.content_object.pk
            ).update(updated=timezone.now())

        if instance.pending_moderation:
            service.send_moderation_required_notification()
        else:
            service.send_notifications()
    else:
        mentions = cache.get("user.%d.comment_pre_save_mentions" % instance.author.pk, [])

    if isinstance(instance.content_object, Image):
        ImageService(instance.content_object).update_comment_count()

    service.send_mention_notifications(mentions)


post_save.connect(nested_comment_post_save, sender=NestedComment)


@receiver(post_delete, sender=NestedComment)
def nested_comment_post_delete(sender, instance, **kwargs):
    if isinstance(instance.content_object, Image):
        ImageService(instance.content_object).update_comment_count()


def toggleproperty_post_delete(sender, instance, **kwargs):
    log.debug(f"toggleproperty_post_delete: {instance.pk}/{instance.user.username}/{instance.property_type}/{instance.content_object}")
    if isinstance(instance.content_object, Image) and not instance.content_object.deleted:
        ImageService(instance.content_object).update_toggleproperty_count(instance.property_type)
        compute_image_index.apply_async(args=(instance.content_object.user.pk,), countdown=10)

        if not instance.content_object.is_wip:
            SearchIndexUpdateService.update_index(instance.content_object)
            SearchIndexUpdateService.update_index(instance.content_object.user, 3600)
            for collaborator in instance.content_object.collaborators.all().iterator():
                compute_image_index.apply_async(args=(collaborator.pk,), countdown=10)
                SearchIndexUpdateService.update_index(collaborator, 3600)
    elif isinstance(instance.content_object, Post):
        compute_contribution_index.apply_async(args=(instance.content_object.user.pk,), countdown=10)
    elif isinstance(instance.content_object, NestedComment):
        compute_contribution_index.apply_async(args=(instance.content_object.author.pk,), countdown=10)
    elif isinstance(instance.content_object, User) and instance.property_type == "follow":
        UserService(instance.content_object).update_followers_count()
        UserService(instance.user).update_following_count()

    if instance.property_type == 'follow':
        unfollow(instance.user, instance.content_object)


post_delete.connect(toggleproperty_post_delete, sender=ToggleProperty)


def toggleproperty_post_save(sender, instance, created, **kwargs):
    log.debug(f"toggleproperty_post_save: {instance.pk}/{instance.user.username}/{instance.property_type}/{instance.content_object}")
    if isinstance(instance.content_object, Image):
        Image.all_objects.filter(pk=instance.object_id).update(updated=timezone.now())

        if not instance.content_object.is_wip:
            SearchIndexUpdateService.update_index(instance.content_object)
            SearchIndexUpdateService.update_index(instance.content_object.user, 3600)
            for collaborator in instance.content_object.collaborators.all().iterator():
                SearchIndexUpdateService.update_index(collaborator, 3600)
    elif isinstance(instance.content_object, Post):
        compute_contribution_index.apply_async(args=(instance.content_object.user.pk,), countdown=10)
    elif isinstance(instance.content_object, NestedComment):
        compute_contribution_index.apply_async(args=(instance.content_object.author.pk,), countdown=10)
    elif isinstance(instance.content_object, User) and instance.property_type == "follow":
        UserService(instance.content_object).update_followers_count()
        UserService(instance.user).update_following_count()

    if created:
        verb = None
        like_count = None
        bookmark_count = None
        comment_count = None

        if instance.property_type in ("like", "bookmark"):

            if instance.content_type == ContentType.objects.get_for_model(Image):
                image = instance.content_type.get_object_for_this_type(id=instance.object_id)
                Image.all_objects.filter(pk=instance.object_id).update(updated=timezone.now())
                ImageService(instance.content_object).update_toggleproperty_count(instance.property_type)
                compute_image_index.apply_async(args=(instance.content_object.user.pk,), countdown=10)

                for x in instance.content_object.collaborators.all():
                    compute_image_index.apply_async(args=(x.pk,), countdown=10)

                if image.is_wip:
                    return

                like_count = ToggleProperty.objects.toggleproperties_for_object('like', image).count()
                bookmark_count = ToggleProperty.objects.toggleproperties_for_object('bookmark', image).count()
                comment_count = NestedComment.objects.filter(
                    content_type=instance.content_type,
                    object_id=image.pk,
                    deleted=False
                ).count()

                if instance.property_type == "like":
                    verb = ACTSTREAM_VERB_LIKED_IMAGE
                elif instance.property_type == "bookmark":
                    verb = ACTSTREAM_VERB_BOOKMARKED_IMAGE
                else:
                    return

                collaborators = [instance.content_object.user] + list(instance.content_object.collaborators.all())

                if instance.user in collaborators:
                    return

                push_notification(
                    collaborators, instance.user, 'new_' + instance.property_type,
                    {
                        'url': build_notification_url(
                            settings.BASE_URL + instance.content_object.get_absolute_url(), instance.user
                        ),
                        'preheader': instance.content_object.title,
                        'title': instance.content_object.title,
                        'user': instance.user.userprofile.get_display_name(),
                        'user_url': settings.BASE_URL + reverse_url(
                            'user_page', kwargs={'username': instance.user.username}
                        ),
                    }
                )

            elif instance.content_type == ContentType.objects.get_for_model(NestedComment):
                push_notification(
                    [instance.content_object.author], instance.user, 'new_comment_like',
                    {
                        'url': build_notification_url(
                            settings.BASE_URL + instance.content_object.get_absolute_url(), instance.user
                        ),
                        'user': instance.user.userprofile.get_display_name(),
                        'user_url': settings.BASE_URL + reverse_url(
                            'user_page', kwargs={'username': instance.user.username}
                        ),
                        'comment': instance.content_object.text,
                        'target': str(instance.content_object.content_object),
                        'target_url': build_notification_url(
                            settings.BASE_URL + instance.content_object.content_object.get_absolute_url(),
                            instance.user
                        ),
                    }
                )

                UserProfile.all_objects.filter(user=instance.content_object.author).update(updated=timezone.now())

            elif instance.content_type == ContentType.objects.get_for_model(Post):
                push_notification(
                    [instance.content_object.user], instance.user, 'new_forum_post_like',
                    {
                        'url': build_notification_url(
                            settings.BASE_URL + instance.content_object.get_absolute_url(), instance.user
                        ),
                        'user': instance.user.userprofile.get_display_name(),
                        'user_url': settings.BASE_URL + reverse_url(
                            'user_page', kwargs={'username': instance.user.username}
                        ),
                        'preheader': instance.content_object.topic.name,
                        'post': instance.content_object.topic.name
                    }
                )

                UserProfile.all_objects.filter(user=instance.content_object.user).update(updated=timezone.now())

            if verb is not None:
                add_story(
                    instance.user,
                    verb=verb,
                    action_object=instance.content_object,
                    like_count=like_count,
                    bookmark_count=bookmark_count,
                    comment_count=comment_count,
                )

        elif instance.property_type == "follow":
            user_ct = ContentType.objects.get_for_model(User)
            if instance.content_type == user_ct:
                followed_user = user_ct.get_object_for_this_type(pk=instance.object_id)
                push_notification(
                    [followed_user], instance.user, 'new_follower', {
                        'object': instance.user.userprofile.get_display_name(),
                        'object_url': build_notification_url(
                            settings.BASE_URL + reverse_url(
                                'user_page', kwargs={'username': instance.user.username}
                            ), instance.user
                        ),
                    }
                )

            follow(instance.user, instance.content_object, send_action=False, actor_only=False)


post_save.connect(toggleproperty_post_save, sender=ToggleProperty)


def create_auth_token(sender, instance, created, **kwargs):
    if created:
        Token.objects.get_or_create(user=instance)


post_save.connect(create_auth_token, sender=User)


def solution_pre_save(sender, instance, **kwargs):
    try:
        solution_before_save = Solution.objects.get(pk=instance.pk)
    except Solution.DoesNotExist:
        return

    if solution_before_save.status >= instance.status:
        return

    if instance.status == Solver.FAILED and instance.attempts >= 1:
        notification = 'image_not_solved'
    elif instance.status == Solver.SUCCESS:
        notification = 'image_solved'
    elif instance.status == Solver.ADVANCED_SUCCESS:
        notification = 'image_solved_advanced'
    elif instance.status == Solver.ADVANCED_FAILED and instance.attempts >= 1:
        notification = 'image_not_solved_advanced'
    else:
        return

    ct = instance.content_type

    try:
        target = ct.get_object_for_this_type(pk=instance.object_id)
    except ct.model_class().DoesNotExist:
        return

    if ct.model == 'image':
        user = target.user
        title = target.title
        thumb = target.thumbnail_raw('gallery', '0', sync=True)
    elif ct.model == 'imagerevision':
        user = target.image.user
        title = target.image.title
        thumb = target.image.thumbnail_raw('gallery', target.label, sync=True)
    else:
        return

    push_notification(
        [user],
        None,
        notification,
        {
            'object_url': build_notification_url(settings.BASE_URL + target.get_absolute_url()),
            'preheader': title,
            'title': title,
            'image_thumbnail': thumb.url if thumb else None,
        }
    )


pre_save.connect(solution_pre_save, sender=Solution)


@receiver(post_save, sender=Solution)
def solution_post_save(sender, instance, created, **kwargs):
    is_solved: bool = instance.status >= Solver.SUCCESS
    model: str = instance.content_type.model
    is_image: bool = model == 'image'
    is_imagerevision: bool = model == 'imagerevision'
    image: Image = None

    if is_image:
        try:
            image = Image.objects_including_wip.get(pk=instance.object_id)
        except Image.DoesNotExist:
            pass
    elif is_imagerevision:
        try:
            revision = ImageRevision.objects.get(pk=instance.object_id)
            image = revision.image
        except ImageRevision.DoesNotExist:
            pass

    if image:
        Image.objects_including_wip.filter(pk=image.pk).update(
            updated=timezone.now(),
        )

    if is_solved:
        constellation = ImageService.get_constellation(instance)
        if constellation:
            log.debug(f"Setting constellation {constellation.get('name')} for {model} {instance.object_id}")

            if is_image:
                Image.objects_including_wip.filter(
                    pk=instance.object_id
                ).update(
                    constellation=constellation.get('abbreviation')
                )
            elif is_imagerevision:
                ImageRevision.objects.filter(
                    pk=instance.object_id
                ).update(
                    constellation=constellation.get('abbreviation')
                )
        else:
            log.debug(f"Could not find constellation for {model} {instance.object_id}")


@receiver(pre_delete, sender=Solution)
def solution_pre_delete(sender, instance, **kwargs):
    if instance.content_type.model == 'image':
        log.debug(f"Removing constellation for image {instance.object_id}")
        Image.objects_including_wip.filter(pk=instance.object_id).update(constellation=None)


def subscription_paid(sender, **kwargs):
    subscription = kwargs.get('subscription')
    user = kwargs.get('user')

    UserProfile.all_objects.filter(user=user).update(updated=timezone.now())
    PremiumService(user).clear_subscription_status_cache_keys()
    UserService(user).update_premium_counter_on_subscription(subscription)
    UserService(user).start_platesolving_tasks()

    if subscription.recurrence_unit is not None:
        return

    if 'premium' in subscription.category and Transaction.objects.filter(
            user=user,
            event='new usersubscription',
            timestamp__gte=DateTimeService.now() - datetime.timedelta(minutes=5)
    ):
        push_notification(
            [user],
            None,
            'new_subscription',
            {
                'BASE_URL': settings.BASE_URL,
                'subscription': subscription
            }
        )
    else:
        push_notification(
            [user],
            None,
            'new_payment',
            {
                'BASE_URL': settings.BASE_URL,
                'subscription': subscription
            }
        )


paid.connect(subscription_paid)


def subscription_signed_up(sender, **kwargs):
    subscription: Subscription = kwargs.get('subscription')
    user_subscription: UserSubscription = kwargs.get('usersubscription')
    user: User = kwargs.get('user')

    UserProfile.all_objects.filter(user=user).update(updated=timezone.now())
    PremiumService(user).clear_subscription_status_cache_keys()
    UserService(user).update_premium_counter_on_subscription(subscription)

    if 'premium' in subscription.category:
        # Deactivate other premium subscriptions
        UserSubscription.active_objects.filter(
            user=user_subscription.user,
            subscription__category__startswith='premium'
        ).exclude(
            pk=user_subscription.pk
        ).update(
            active=False
        )

        if subscription.recurrence_unit is None:
            # When there's a payment for an expired subscription, make sure we start the subscription from today.
            today = DateTimeService.today()
            if user_subscription.expires is None or user_subscription.expires < today:
                user_subscription.expires = today

            # Non-recurring premium subscription are for a year, no exceptions.
            user_subscription.expires = extend_date_by(user_subscription.expires, 1, 'Y')
            # Non-recurring subscription are of course cancelled because they are not recurring.
            user_subscription.cancelled = True
            user_subscription.save()

        # Invalidate other premium subscriptions
        UserSubscription.active_objects \
            .filter(
            user=user_subscription.user,
            subscription__category__startswith='premium'
        ) \
            .exclude(pk=user_subscription.pk) \
            .update(active=False)

        if Transaction.objects.filter(
                user=user,
                event='new usersubscription',
                timestamp__gte=DateTimeService.now() - datetime.timedelta(minutes=5)
        ):
            push_notification(
                [user],
                None,
                'new_subscription',
                {
                    'BASE_URL': settings.BASE_URL,
                    'subscription': subscription
                }
            )
        else:
            push_notification(
                [user],
                None,
                'new_payment',
                {
                    'BASE_URL': settings.BASE_URL,
                    'subscription': subscription
                }
            )


signed_up.connect(subscription_signed_up)


def subscription_unsubscribed(sender, **kwargs):
    subscription: Subscription = kwargs.get('subscription')
    user: User = kwargs.get('user')

    UserProfile.all_objects.filter(user=user).update(updated=timezone.now())
    PremiumService(user).clear_subscription_status_cache_keys()

    push_notification(
        [user],
        None,
        'subscription_canceled',
        {
            'BASE_URL': settings.BASE_URL,
            'subscription': subscription
        }
    )


unsubscribed.connect(subscription_unsubscribed)


def user_subscription_post_delete(sender, instance, **kwargs):
    try:
        PremiumService(instance.user).clear_subscription_status_cache_keys()
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        pass


post_delete.connect(user_subscription_post_delete, sender=UserSubscription)


def user_subscription_post_save(sender, instance, created, **kwargs):
    try:
        PremiumService(instance.user).clear_subscription_status_cache_keys()
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        pass


post_save.connect(user_subscription_post_save, sender=UserSubscription)


def group_pre_save(sender, instance, **kwargs):
    try:
        group = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass
    else:
        # Group is becoming autosubmission
        if not group.autosubmission and instance.autosubmission:
            instance.images.clear()
            images = Image.objects.filter(user__in=instance.members.all())
            for image in images:
                instance.images.add(image)

        # Group was renamed
        if group.name != instance.name:
            group.forum.name = instance.name
            group.forum.save()


pre_save.connect(group_pre_save, sender=Group)


def group_post_save(sender, instance, created, **kwargs):
    if created and instance.creator is not None:
        instance.members.add(instance.creator)
        if instance.moderated:
            instance.moderators.add(instance.creator)

        if instance.public:
            followers = [
                x.user for x in
                ToggleProperty.objects.toggleproperties_for_object(
                    "follow", UserProfile.objects.get(user__pk=instance.creator.pk).user
                )
            ]
            push_notification(
                followers, instance.creator, 'new_public_group_created',
                {
                    'creator': instance.creator.userprofile.get_display_name(),
                    'preheader': instance.name,
                    'group_name': instance.name,
                    'url': settings.BASE_URL + reverse_url('group_detail', args=(instance.pk,)),
                }
            )

            add_story(
                instance.creator,
                verb=ACTSTREAM_VERB_CREATED_PUBLIC_GROUP,
                action_object=instance
            )


post_save.connect(group_post_save, sender=Group)


def group_members_changed(sender, instance, **kwargs):
    action = kwargs['action']
    pk_set = kwargs['pk_set']

    if pk_set:
        UserProfile.objects.filter(user__pk__in=pk_set).update(updated=timezone.now())

    group_sync_map = {
        'IOTD Submitters': [GroupName.IOTD_SUBMITTERS, 'content_moderators', GroupName.IOTD_STAFF],
        'IOTD Reviewers': [GroupName.IOTD_REVIEWERS, 'content_moderators', GroupName.IOTD_STAFF],
        'IOTD Judges': [GroupName.IOTD_JUDGES, 'content_moderators', GroupName.IOTD_STAFF],
    }
    if instance.name in list(group_sync_map.keys()):
        for django_group in group_sync_map[instance.name]:
            DjangoGroup.objects.get_or_create(name=django_group)
        django_groups = DjangoGroup.objects.filter(name__in=group_sync_map[instance.name])
    try:
        iotd_staff_group = Group.objects.get(name='IOTD Staff')
    except Group.DoesNotExist:
        iotd_staff_group = None

    if action == 'post_add':
        users = [profile.user for profile in UserProfile.objects.filter(user__pk__in=pk_set)]
        instance.save()  # trigger date_updated update

        if instance.public:
            for pk in pk_set:
                user = UserProfile.objects.get(user__pk=pk).user
                if user != instance.owner:
                    followers = [
                        x.user for x in
                        ToggleProperty.objects.toggleproperties_for_object("follow", user)
                    ]
                    push_notification(
                        sorted(list(set(followers + [instance.owner])), key=lambda x: x.pk),
                        user,
                        'user_joined_public_group',
                        {
                            'user': user.userprofile.get_display_name(),
                            'user_url': build_notification_url(
                                settings.BASE_URL + reverse_url('user_page', kwargs={'username': user.username}),
                                user
                            ),
                            'preheader': instance.name,
                            'group_name': instance.name,
                            'url': build_notification_url(
                                settings.BASE_URL + reverse_url('group_detail', args=(instance.pk,)),
                                user
                            ),
                        }
                    )

                    add_story(
                        user,
                        verb=ACTSTREAM_VERB_JOINED_GROUP,
                        action_object=instance
                    )

        if instance.autosubmission:
            for batch_pk_set in batch(pk_set, size=50):
                images = Image.objects_including_wip.filter(user__pk__in=batch_pk_set)
                for image in images:
                    instance.images.add(image)

        # Sync IOTD AstroBin groups with django groups
        if instance.name in list(group_sync_map.keys()):
            for user in users:
                UserProfile.objects.filter(user=user).update(
                    insufficiently_active_iotd_staff_member_reminders_sent=0
                )

            for django_group in django_groups:
                django_group.user_set.add(*list(users))
            if iotd_staff_group:
                for user in users:
                    iotd_staff_group.members.add(user)

    elif action == 'post_remove':
        users = [profile.user for profile in UserProfile.objects.filter(user__pk__in=pk_set)]
        for batch_pk_set in batch(pk_set, size=50):
            images = Image.objects_including_wip.filter(user__pk__in=batch_pk_set)
            for image in images:
                instance.images.remove(image)

        if instance.forum and not instance.public:
            topics = Topic.objects.filter(forum=instance.forum)
            for topic in topics:
                topic.subscribers.remove(*User.objects.filter(pk__in=kwargs['pk_set']))

        # Sync IOTD AstroBin groups with django groups
        if instance.name in list(group_sync_map.keys()):
            all_members = []
            all_members_chain = chain(
                [
                    x.members.all()
                    for x in Group.objects \
                    .filter(name__in=list(group_sync_map.keys())) \
                    .exclude(name=instance.name)
                ]
            )
            for chain_item in all_members_chain:
                all_members += chain_item
            for user in [x for x in users if x not in all_members]:
                for django_group in django_groups:
                    django_group.user_set.remove(user)
                if iotd_staff_group:
                    iotd_staff_group.members.remove(user)

    elif action == 'pre_clear':
        # Sync IOTD AstroBin groups with django groups
        users = instance.members.all()
        if instance.name in list(group_sync_map.keys()):
            all_members = []
            all_members_chain = chain(
                [
                    x.members.all()
                    for x in Group.objects \
                    .filter(name__in=list(group_sync_map.keys())) \
                    .exclude(name=instance.name)
                ]
            )
            for chain_item in all_members_chain:
                all_members += chain_item
            for user in [x for x in users if x not in all_members]:
                for django_group in django_groups:
                    django_group.user_set.remove(user)
                if iotd_staff_group:
                    iotd_staff_group.members.remove(user)

    elif action == 'post_clear':
        instance.images.clear()


m2m_changed.connect(group_members_changed, sender=Group.members.through)


def group_images_changed(sender, instance, **kwargs):
    if kwargs['action'] == 'post_add' and 'pk_set' in kwargs:
        group = sender.group.get_queryset().first()
        group.save()  # trigger date_updated update


m2m_changed.connect(group_images_changed, sender=Group.images.through)


def legacy_equipment_changed(sender, instance: Image, **kwargs):
    Image.all_objects.filter(pk=instance.pk).update(updated=timezone.now())


m2m_changed.connect(legacy_equipment_changed, sender=Image.imaging_telescopes.through)
m2m_changed.connect(legacy_equipment_changed, sender=Image.imaging_cameras.through)
m2m_changed.connect(legacy_equipment_changed, sender=Image.mounts.through)
m2m_changed.connect(legacy_equipment_changed, sender=Image.filters.through)
m2m_changed.connect(legacy_equipment_changed, sender=Image.focal_reducers.through)
m2m_changed.connect(legacy_equipment_changed, sender=Image.accessories.through)
m2m_changed.connect(legacy_equipment_changed, sender=Image.software.through)
m2m_changed.connect(legacy_equipment_changed, sender=Image.guiding_telescopes.through)
m2m_changed.connect(legacy_equipment_changed, sender=Image.guiding_cameras.through)


def new_equipment_changed(sender, instance: Image, **kwargs):
    model_class = kwargs.pop('model')
    pk_set: Set[int] = kwargs.pop('pk_set')
    action = kwargs.pop('action')
    now = timezone.now()
    update_deadline = now - datetime.timedelta(seconds=3)
    index_update_deadline = now - datetime.timedelta(hours=12)

    def update_indexes(item):
        if not item.last_added_or_removed_from_image or item.last_added_or_removed_from_image < index_update_deadline:
            SearchIndexUpdateService.update_index(item)
            if item.brand is not None:
                if not item.brand.last_added_or_removed_from_image or \
                        item.brand.last_added_or_removed_from_image < index_update_deadline:
                    SearchIndexUpdateService.update_index(item.brand)
                EquipmentBrand.objects.filter(pk=item.brand.pk).update(last_added_or_removed_from_image=now)

    Image.all_objects.filter(pk=instance.pk).update(updated=timezone.now())
    if not instance.is_wip:
        SearchIndexUpdateService.update_index(instance)
        SearchIndexUpdateService.update_index(instance.user)

    if action == 'pre_clear':
        item_ids = sender.objects.filter(image=instance).values_list(model_class.__name__.lower(), flat=True)
        items = model_class.objects.filter(pk__in=list(item_ids))
        for item in items.iterator():
            update_indexes(item)
        items.update(last_added_or_removed_from_image=now)
    elif action == 'post_remove':
        for pk in pk_set:
            item = get_object_or_None(model_class, pk=pk)
            if item is not None:
                ImageEquipmentLog.objects.create(
                    image=instance,
                    equipment_item=item,
                    verb=ImageEquipmentLog.REMOVED
                )
                update_indexes(item)
                if not item.last_added_or_removed_from_image or item.last_added_or_removed_from_image < update_deadline:
                    model_class.objects.filter(pk=pk).update(last_added_or_removed_from_image=now)
    elif action == 'post_add':
        for pk in pk_set:
            item = get_object_or_None(model_class, pk=pk)
            if item is not None:
                ImageEquipmentLog.objects.create(
                    image=instance,
                    equipment_item=item,
                    verb=ImageEquipmentLog.ADDED
                )
                update_indexes(item)
                if not item.last_added_or_removed_from_image or item.last_added_or_removed_from_image < update_deadline:
                    model_class.objects.filter(pk=pk).update(last_added_or_removed_from_image=now)


m2m_changed.connect(new_equipment_changed, sender=Image.imaging_telescopes_2.through)
m2m_changed.connect(new_equipment_changed, sender=Image.imaging_cameras_2.through)
m2m_changed.connect(new_equipment_changed, sender=Image.mounts_2.through)
m2m_changed.connect(new_equipment_changed, sender=Image.filters_2.through)
m2m_changed.connect(new_equipment_changed, sender=Image.accessories_2.through)
m2m_changed.connect(new_equipment_changed, sender=Image.software_2.through)
m2m_changed.connect(new_equipment_changed, sender=Image.guiding_telescopes_2.through)
m2m_changed.connect(new_equipment_changed, sender=Image.guiding_cameras_2.through)


def group_post_delete(sender, instance, **kwargs):
    try:
        instance.forum.delete()
    except Forum.DoesNotExist:
        pass


post_delete.connect(group_post_delete, sender=Group)


# TODO: move these and other related signal handlers to astrobin_apps_forum
def forum_topic_pre_save(sender, instance, **kwargs):
    try:
        topic = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    if topic.forum != instance.forum:
        # This topic is being moved to another forum
        log.debug(
            "Topic '%s' moved from '%s' to '%s'" % (
                instance.name,
                topic.forum.name,
                instance.forum.name)
        )

        equipment_item: EquipmentItem = ForumService(instance.forum).get_equipment_item()
        group: Group = instance.forum.group if hasattr(instance.forum, 'group') else None

        push_notification(
            [instance.user],
            None,
            'topic_moved',
            {
                'topic_url': build_notification_url(settings.BASE_URL + instance.get_absolute_url(), instance.user),
                'topic_name': topic.name,
                'old_forum_name': topic.forum.name,
                'new_forum_name': instance.forum.name,
                'group_url': build_notification_url(
                    settings.BASE_URL + reverse_url('group_detail', kwargs={'pk': group.pk}), instance.user
                ) if group else None,
                'group_name': group.name if group else None,
                'equipment_item_name': f'{equipment_item.brand.name if equipment_item.brand else gettext("(DIY)")} {equipment_item.name}' if equipment_item else None,
                'equipment_item_url': build_notification_url(
                    AppRedirectionService.redirect(
                        f'/equipment/explorer/{EquipmentItemService(equipment_item).get_type()}/{equipment_item.pk}'
                    )
                ) if equipment_item else None,
                'preheader': instance.name,
                'topic_title': instance.name,
            },
        )

        ForumService.create_topic_redirect(
            instance.forum.category.slug,
            instance.forum.slug,
            instance.slug,
            topic
        )

        if instance.forum.category.slug == 'equipment-forums' and not instance.on_moderation:
            notify_equipment_users.apply_async(args=(instance.pk,), countdown=10)

    if topic.on_moderation and not instance.on_moderation:
        # This topic is being approved

        if hasattr(instance.forum, 'group'):
            group = instance.forum.group
            push_notification(
                [x for x in group.members.all() if x != instance.user],
                instance.user,
                'new_topic_in_group',
                {
                    'user_url': build_notification_url(
                        settings.BASE_URL + reverse_url('user_page', kwargs={'username': instance.user})
                    ),
                    'user': instance.user.userprofile.get_display_name(),
                    'url': build_notification_url(settings.BASE_URL + instance.get_absolute_url(), instance.user),
                    'group_url': build_notification_url(
                        reverse_url('group_detail', kwargs={'pk': group.pk}), instance.user
                    ),
                    'group_name': group.name,
                    'preheader': instance.name,
                    'topic_title': instance.name,
                },
            )
        elif instance.forum.category.slug == 'equipment-forums':
            notify_equipment_users.delay(instance.pk)


pre_save.connect(forum_topic_pre_save, sender=Topic)


def forum_topic_post_save(sender, instance, created, **kwargs):
    if created:
        if hasattr(instance.forum, 'group'):
            group = instance.forum.group

            if instance.on_moderation:
                recipients = group.moderators.all()
            else:
                recipients = group.members.all()
            recipients = [x for x in recipients if x != instance.user]

            push_notification(
                recipients,
                instance.user,
                'new_topic_in_group',
                {
                    'user_url': build_notification_url(
                        settings.BASE_URL + reverse_url('user_page', kwargs={'username': instance.user})
                    ),
                    'user': instance.user.userprofile.get_display_name(),
                    'url': build_notification_url(settings.BASE_URL + instance.get_absolute_url(), instance.user),
                    'group_url': build_notification_url(
                        settings.BASE_URL + reverse_url('group_detail', kwargs={'pk': group.pk}), instance.user
                    ),
                    'group_name': group.name,
                    'preheader': instance.name,
                    'topic_title': instance.name,
                },
            )
        elif instance.forum.category.slug == 'equipment-forums':
            if not instance.on_moderation:
                notify_equipment_users.delay(instance.pk)

    cache.delete(ForumService.home_page_latest_from_forum_cache_key(instance.user))


post_save.connect(forum_topic_post_save, sender=Topic)


def forum_post_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            previous_mentions = MentionsService.get_mentions(sender.objects.get(pk=instance.pk).body)
            current_mentions = MentionsService.get_mentions(instance.body)
            if Post.objects.filter(pk=instance.pk, on_moderation=True).exists():
                mentions = current_mentions
            else:
                mentions = [
                    item for item in current_mentions
                    if item not in previous_mentions and item != instance.user.username
                ]
        except sender.DoesNotExist:
            mentions = []

        cache.set("post.%d.forum_post_pre_save_mentions" % instance.pk, mentions, 2)

        if not instance.on_moderation and Post.objects.filter(pk=instance.pk, on_moderation=True).exists():
            cache.set("post.%d.forum_post_pre_save_approved" % instance.pk, True, 2)

    for attribute in ['body', 'body_text', 'body_html']:
        for language in settings.LANGUAGES:
            with override(language[0]):
                for message in [
                    '*** Type your message here ***',
                    '*** Type your forum post here ***',
                    '*** Type your reply here ***',
                ]:
                    translated = gettext(message)
                    content = getattr(instance, attribute)
                    setattr(
                        instance,
                        attribute,
                        content.replace(translated, '')
                    )

        content = getattr(instance, attribute)
        re.sub(r'\n+', '\n', content).strip()
        setattr(instance, attribute, content)


pre_save.connect(forum_post_pre_save, sender=Post)


def forum_post_post_save(sender, instance, created, **kwargs):
    def notify_subscribers(mentions: List[str]) -> None:
        recipients = list(
            instance.topic.subscribers.exclude(
                pk__in=list(
                    set(
                        [instance.user.pk, instance.topic.user.pk] +
                        [x.pk for x in MentionsService.get_mentioned_users_with_notification_enabled(
                            mentions, 'new_forum_post_mention'
                        )
                         ]
                    )
                )
            )
        )

        if (
                instance.topic.user != instance.user and
                instance.topic.user.username not in mentions and
                instance.topic.subscribers.filter(pk=instance.topic.user.pk).exists()
        ):
            push_notification(
                [instance.topic.user],
                instance.user,
                'new_forum_reply_started_topic',
                {
                    'user': instance.user.userprofile.get_display_name(),
                    'user_url': settings.BASE_URL + reverse_url('user_page', kwargs={'username': instance.user}),
                    'post_url': build_notification_url(settings.BASE_URL + instance.get_absolute_url(), instance.user),
                    'topic_url': build_notification_url(
                        settings.BASE_URL + instance.topic.get_absolute_url(), instance.user
                    ),
                    'preheader': instance.topic.name,
                    'topic_name': instance.topic.name,
                    'unsubscribe_url': build_notification_url(
                        settings.BASE_URL + reverse_url('pybb:delete_subscription', args=[instance.topic.id]),
                        instance.user
                    )
                }
            )

        if recipients:
            push_notification(
                recipients,
                instance.user,
                'new_forum_reply',
                {
                    'preheader': instance.topic.name,
                    'user': instance.user.userprofile.get_display_name(),
                    'user_url': settings.BASE_URL + reverse_url('user_page', kwargs={'username': instance.user}),
                    'post_url': build_notification_url(settings.BASE_URL + instance.get_absolute_url(), instance.user),
                    'topic_url': build_notification_url(
                        settings.BASE_URL + instance.topic.get_absolute_url(), instance.user
                    ),
                    'topic_name': instance.topic.name,
                    'unsubscribe_url': build_notification_url(
                        settings.BASE_URL + reverse_url('pybb:delete_subscription', args=[instance.topic.id]),
                        instance.user
                    )
                }
            )

    def notify_mentioned(mentions: List[str]) -> None:
        for username in mentions:
            user = get_object_or_None(User, username=username)
            if user is None:
                try:
                    profile = get_object_or_None(UserProfile, real_name=username)
                    if profile:
                        user = profile.user
                except MultipleObjectsReturned:
                    user = None
            if user:
                push_notification(
                    [user],
                    instance.user,
                    'new_forum_post_mention',
                    {
                        'url': build_notification_url(settings.BASE_URL + instance.get_absolute_url(), instance.user),
                        'user': instance.user.userprofile.get_display_name(),
                        'user_url': settings.BASE_URL + reverse_url(
                            'user_page', kwargs={'username': instance.user}
                        ),
                        'preheader': instance.topic.name,
                        'post': instance.topic.name,
                    }
                )

    compute_contribution_index.apply_async(args=(instance.user.pk,), countdown=10)

    if created:
        if hasattr(instance.topic.forum, 'group'):
            instance.topic.forum.group.save()  # trigger date_updated update

        if get_pybb_profile(instance.user).autosubscribe and \
                perms.may_subscribe_topic(instance.user, instance.topic):
            instance.topic.subscribers.add(instance.user)

        mentions = [x for x in MentionsService.get_mentions(instance.body) if x != instance.user.username]
        if not instance.on_moderation:
            notify_subscribers(mentions)
            notify_mentioned(mentions)
        else:
            NotificationsService.email_superusers(
                'New forum post needs moderation',
                '%s%s' % (settings.BASE_URL, instance.get_absolute_url())
            )
    else:
        mentions = cache.get("post.%d.forum_post_pre_save_mentions" % instance.pk, [])
        cache.delete("post.%d.forum_post_pre_save_mentions" % instance.pk)
        if cache.get("post.%d.forum_post_pre_save_approved" % instance.pk):
            push_notification(
                [instance.user], None, 'forum_post_approved', {
                    'preheader': instance.topic.name,
                    'url': build_notification_url(settings.BASE_URL + instance.get_absolute_url())
                }
            )
            notify_subscribers(mentions)
            notify_mentioned(mentions)
            cache.delete("post.%d.forum_post_pre_save_approved" % instance.pk)

    cache.delete(ForumService.home_page_latest_from_forum_cache_key(instance.user))


post_save.connect(forum_post_post_save, sender=Post)


@receiver(post_delete, sender=Post)
def forum_post_post_delete(sender, instance, **kwargs):
    compute_contribution_index.apply_async(args=(instance.user.pk,), countdown=10)


@receiver(post_save, sender=TopicReadTracker)
def topic_read_tracker_post_save(sender, instance, created, **kwargs):
    cache.delete(ForumService.home_page_latest_from_forum_cache_key(instance.user))


def user_pre_save(sender, instance, **kwargs):
    if instance.pk:
        original_instance = sender.objects.get(pk=instance.pk)
        if original_instance.email != instance.email and instance.userprofile.stripe_customer_id:
            stripe.api_key = settings.STRIPE['keys']['secret']
            try:
                customer = stripe.Customer.retrieve(instance.userprofile.stripe_customer_id)
                if customer.email != instance.email:
                    customer.email = instance.email
                    customer.save()
            except StripeError as e:
                log.error('Error updating Stripe customer: %s' % e)


pre_save.connect(user_pre_save, sender=User)


def user_post_save(sender, instance, created, **kwargs):
    UserProfile.objects.filter(user=instance).update(updated=timezone.now())


post_save.connect(user_post_save, sender=User)


def user_pre_delete(sender, instance, **kwargs):
    user_ct = ContentType.objects.get_for_model(User)
    ToggleProperty.objects.filter(user=instance, property_type__in=['follow', 'bookmark']).delete()
    ToggleProperty.objects.filter(content_type=user_ct, object_id=instance.pk, property_type='follow').delete()

    try:
        if getattr(instance, 'userprofile') and instance.userprofile.stripe_customer_id:
            stripe.api_key = settings.STRIPE['keys']['secret']
            stripe.Customer.delete(instance.userprofile.stripe_customer_id)
    except StripeError as e:
        log.error('Error deleting Stripe customer: %s' % e)
    except ObjectDoesNotExist as e:
        log.error('User %s has no userprofile: %s' % (instance.username, str(e)))


pre_delete.connect(user_pre_delete, sender=User)


@receiver(pre_save, sender=UserProfile)
def userprofile_pre_save(sender, instance: UserProfile, **kwargs):
    try:
        before_save: UserProfile = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        # Object is new, so all fields are "changed"
        return

    if before_save.skill_level != instance.skill_level:
        instance.skill_level_updated = DateTimeService.now()

    if before_save.receive_newsletter != instance.receive_newsletter:
        service: MailingListService = MailingListService(instance.user)
        list_id: int = settings.BREVO_NEWSLETTER_LIST_ID
        if instance.receive_newsletter:
            service.subscribe(list_id)
        else:
            service.unsubscribe(list_id)


@receiver(post_softdelete, sender=UserProfile)
def userprofile_post_softdelete(sender, instance, **kwargs):
    MailingListService(instance.user).delete_contact()

    # Images are attached to the auth.User object, and that's not really
    # deleted, so nothing is cascaded, hence the following line.
    instance.user.is_active = False

    if instance.user.email and 'ASTROBIN_IGNORE' not in instance.user.email:
        instance.user.email = instance.user.email.replace('@', '+ASTROBIN_IGNORE@')

    instance.user.save()

    Image.objects_including_wip.filter(user=instance.user).delete()
    ImageRevision.objects.filter(image__user=instance.user).delete()
    NestedComment.objects.filter(author=instance.user, deleted=False).update(deleted=True)

    if instance.stripe_subscription_id:
        stripe.api_key = settings.STRIPE['keys']['secret']
        try:
            stripe.Subscription.cancel(instance.stripe_subscription_id)
        except (StripeError, AttributeError) as e:
            log.error('Error canceling Stripe subscription (%s): %s' % (instance.stripe_subscription_id, e))
            stripe.Subscription.modify(instance.stripe_customer_id, cancel_at_period_end=True)

    UserIndex().remove_object(instance.user)


@receiver(post_undelete, sender=UserProfile)
def userprofile_post_undelete(sender, instance, **kwargs):
    instance.user.is_active = True
    instance.user.email = instance.user.email.replace('+ASTROBIN_IGNORE', '')
    instance.user.save()

    if instance.receive_newsletter:
        MailingListService(instance.user).subscribe(settings.BREVO_NEWSLETTER_LIST_ID)

    UserIndex().update_object(instance.user)


@receiver(pre_delete, sender=UserProfile)
def userprofile_pre_delete(sender, instance: UserProfile, **kwargs):
    if not getattr(instance, DELETED_FIELD_NAME, None):
        try:
            userprofile_post_softdelete(sender, instance, **kwargs)
        except InternalError as e:
            log.error("Error soft deleting user profile %d: %s" % (instance.pk, str(e)))

    for revision in ImageRevision.all_objects.filter(image__user=instance.user):
        log.debug("Deleting revision %d" % revision.pk)
        revision.purge_caches = False
        revision.delete(force_policy=HARD_DELETE)

    for image in Image.all_objects.filter(user=instance.user):
        log.debug("Deleting image %d" % image.pk)
        image.purge_caches = False
        image.delete(force_policy=HARD_DELETE)


@receiver(post_save, sender=Message)
@receiver(post_delete, sender=Message)
def update_notification_cache(sender, instance, **kwargs):
    clear_notifications_template_cache(instance.user.username)
    UserProfile.objects.filter(user=instance.user).update(last_notification_update=DateTimeService.now())


def top_pick_nominations_archive_post_save(sender, instance, created, **kwargs):
    if created:
        image = instance.image
        thumb = image.thumbnail_raw('gallery', None, sync=True)

        collaborators = [image.user] + list(image.collaborators.all())
        push_notification(
            collaborators, None, 'your_image_is_tpn', {
                'preheader': image.title,
                'image': image,
                'image_thumbnail': thumb.url if thumb else None
            }
        )


post_save.connect(top_pick_nominations_archive_post_save, sender=TopPickNominationsArchive)


def top_pick_archive_item_post_save(sender, instance, created, **kwargs):
    if created:
        image = instance.image
        thumb = image.thumbnail_raw('gallery', None, sync=True)

        submitters = [x.submitter for x in IotdSubmission.objects.filter(image=image)]
        push_notification(
            submitters, None, 'image_you_promoted_is_tp', {
                'preheader': image.title,
                'image': image,
                'image_thumbnail': thumb.url if thumb else None
            }
        )

        reviewers = [x.reviewer for x in IotdVote.objects.filter(image=image)]
        push_notification(
            reviewers, None, 'image_you_promoted_is_tp', {
                'image': image,
                'image_thumbnail': thumb.url if thumb else None
            }
        )

        dismissers = [x.user for x in IotdDismissedImage.objects.filter(image=image)]
        push_notification(
            dismissers, None, 'image_you_dismissed_is_tp', {
                'preheader': image.title,
                'image': image,
                'image_thumbnail': thumb.url if thumb else None
            }
        )

        collaborators = [image.user] + list(image.collaborators.all())
        push_notification(
            collaborators, None, 'your_image_is_tp', {
                'preheader': image.title,
                'image': image,
                'image_thumbnail': thumb.url if thumb else None
            }
        )


post_save.connect(top_pick_archive_item_post_save, sender=TopPickArchive)


def abuse_report_post_save(sender, instance, created, **kwargs):
    if created:
        NotificationsService.email_superusers(
            'New abuse report',
            '%s/admin/common/abusereport/%d/' % (settings.BASE_URL, instance.pk)
        )

        if AbuseReport.objects.filter(
                content_owner=instance.content_owner
        ).exclude(
            decision=ABUSE_REPORT_DECISION_OVERRULED
        ).count() == 5:
            NotificationsService.email_superusers(
                'User %s received 5 abuse reports' % instance.content_owner,
                '%s/admin/common/abusereport/%d/' % (settings.BASE_URL, instance.pk)
            )


post_save.connect(abuse_report_post_save, sender=AbuseReport)


def camera_rename_proposal_post_save(sender, instance: CameraRenameProposal, created: bool, **kwargs):
    process_camera_rename_proposal.delay(instance.pk)


post_save.connect(camera_rename_proposal_post_save, sender=CameraRenameProposal)


def gear_migration_strategy_post_save(sender, instance: GearMigrationStrategy, created: bool, **kwargs):
    if not created:
        return

    if instance.user:
        approve_migration_strategy.delay(instance.id, instance.migration_flag_moderator.id)
    else:
        gear: Gear = instance.gear
        for usage_data in (
                ('imaging_telescopes', Telescope),
                ('imaging_cameras', Camera),
                ('mounts', Mount),
                ('filters', Filter),
                ('focal_reducers', FocalReducer),
                ('accessories', Accessory),
                ('software', Software),
                ('guiding_telescopes', Telescope),
                ('guiding_cameras', Camera),
        ):
            usage_class = usage_data[0]
            GearKlass = usage_data[1]
            gear_item = get_object_or_None(GearKlass, pk=gear.pk)
            if not gear_item:
                continue
            user_ids = set(
                Image.objects.filter(
                    user__groups__name="own_equipment_migrators",
                    **{usage_class: gear_item}
                ).values_list('user', flat=True)
            )
            for user_id in user_ids:
                user = User.objects.get(id=user_id)
                if not get_object_or_None(GearMigrationStrategy, gear=gear, user=user):
                    GearMigrationStrategy.objects.create(
                        gear=gear,
                        user=user,
                        migration_flag=instance.migration_flag,
                        migration_flag_moderator=instance.migration_flag_moderator,
                        migration_flag_timestamp=timezone.now(),
                        migration_content_object=instance.migration_content_object,
                    )


post_save.connect(gear_migration_strategy_post_save, sender=GearMigrationStrategy)


@receiver(m2m_changed, sender=Image.collaborators.through)
def image_collaborators_changed(sender, instance: Image, **kwargs):
    action = kwargs.pop('action')
    pk_set = kwargs.pop('pk_set')
    thumb = instance.thumbnail_raw('gallery', None, sync=True)

    if action == 'pre_add':
        users = User.objects.filter(pk__in=pk_set)
        for user in users.iterator():
            UserService(user).clear_gallery_image_list_cache()
        push_notification(
            list(users), instance.user, 'added_you_as_collaborator', {
                'preheader': instance.title,
                'image': instance,
                'image_thumbnail': thumb.url if thumb else None
            }
        )
    elif action == 'post_add':
        users = User.objects.filter(pk__in=pk_set)
        for user in users.iterator():
            UserService(user).update_image_count()
            followers = User.objects.filter(
                toggleproperty__content_type=ContentType.objects.get_for_model(user),
                toggleproperty__object_id=user.id,
                toggleproperty__property_type="follow"
            ).distinct()
            push_notification_task.apply_async(
                args=(
                    list(followers.values_list('id', flat=True)),
                    user.id,
                    'new_image',
                    {
                        'preheader': instance.title,
                        'image_id': instance.id,
                        'image_thumbnail': thumb.url if thumb else None
                    }
                )
            )
    elif action == 'pre_remove':
        users = User.objects.filter(pk__in=pk_set)
        for user in users.iterator():
            UserService(user).clear_gallery_image_list_cache()
        push_notification(
            list(users), instance.user, 'removed_as_collaborator', {
                'preheader': instance.title,
                'image': instance,
                'image_thumbnail': thumb.url if thumb else None
            }
        )
    elif action == 'post_remove':
        users = User.objects.filter(pk__in=pk_set)
        for user in users.iterator():
            UserService(user).update_image_count()


@receiver(m2m_changed, sender=Image.pending_collaborators.through)
def image_pending_collaborators_changed(sender, instance: Image, **kwargs):
    action = kwargs.pop('action')
    pk_set = kwargs.pop('pk_set')

    if action == 'pre_add':
        thumb = instance.thumbnail_raw('gallery', None, sync=True)
        users = User.objects.filter(pk__in=pk_set)
        push_notification(
            list(users), instance.user, 'requested_as_collaborator', {
                'preheader': instance.title,
                'image': instance,
                'image_thumbnail': thumb.url if thumb else None
            }
        )
    elif action == 'post_remove':
        for user in User.objects.filter(pk__in=pk_set).iterator():
            if instance.collaborators.filter(pk=user.pk).exists():
                instance.collaborators.remove(user)


@receiver(user_verified)
def on_user_verified(request, user, device, **kwargs):
    country_code = get_client_country_code(request)
    UserService(user).set_last_seen(country_code)


@receiver(pre_save, sender=User)
def on_password_change(sender, **kwargs):
    user = kwargs.get('instance', None)

    if user:
        new_password = user.password
        try:
            old_password = User.objects.get(pk=user.pk).password
        except User.DoesNotExist:
            old_password = None

        if new_password != old_password:
            UserProfile.objects.filter(user=user).update(
                detected_insecure_password=None,
                password_reset_token=None,
            )
            # Clears django-rest-framework tokens
            Token.objects.filter(user=user).delete()


@receiver(m2m_changed, sender=UserProfile.shadow_bans.through)
def remove_follow_on_shadow_ban(sender, instance, **kwargs):
    action = kwargs.pop('action')
    pk_set = kwargs.pop('pk_set')

    if action == 'post_add':
        profiles = UserProfile.objects.filter(pk__in=pk_set)
        for profile in profiles.iterator():
            ToggleProperty.objects.filter(
                user__pk=profile.user.pk,
                property_type='follow',
                content_type=ContentType.objects.get_for_model(profile.user),
                object_id=instance.user.pk
            ).delete()


@receiver(m2m_changed, sender=Collection.images.through)
def update_collection_image_count(sender, instance, action, reverse, model, pk_set, **kwargs):
    def _update_counts(collection):
        collection.image_count = Image.objects_plain.filter(collections=collection).count()
        collection.image_count_including_wip = Image.objects_including_wip_plain.filter(collections=collection).count()
        collection.save()

    if action == "post_add":
        if reverse:
            # This case handles Image.collections.add()
            for pk in pk_set:
                collection = Collection.objects.get(pk=pk)
                _update_counts(collection)
        else:
            # This case handles Collection.images.add()
            _update_counts(instance)

    elif action == "post_remove":
        if reverse:
            # This case handles Image.collections.remove()
            for pk in pk_set:
                collection = Collection.objects.get(pk=pk)
                _update_counts(collection)
        else:
            # This case handles Collection.images.remove()
            _update_counts(instance)

    elif action == "pre_clear":
        if reverse:
            # This case handles Image.collections.clear()
            for collection in Collection.objects.filter(images=instance):
                collection.image_count = 0
                collection.image_count_including_wip = 0
                collection.save()
        else:
            # This case handles Collection.images.clear()
            instance.image_count = 0
            instance.image_count_including_wip = 0
            instance.save()


@receiver(post_save, sender=Collection)
def update_nested_collection_count_on_create(sender, instance: Collection, created: bool, **kwargs):
    if created and instance.parent:
        instance.parent.nested_collection_count += 1
        instance.parent.save()


@receiver(pre_delete, sender=Collection)
def update_nested_collection_count_on_delete(sender, instance: Collection, **kwargs):
    if instance.parent:
        instance.parent.nested_collection_count -= 1
        if instance.parent.nested_collection_count < 0:
            instance.parent.nested_collection_count = 0
        instance.parent.save()


@receiver(avatar_updated, sender=Avatar)
def on_avatar_updated(sender, user, avatar, **kwargs):
    UserProfile.objects.filter(user=user).update(updated=timezone.now())


@receiver(avatar_deleted, sender=Avatar)
def on_avatar_deleted(sender, user, avatar, **kwargs):
    UserProfile.objects.filter(user=user).update(updated=timezone.now())
