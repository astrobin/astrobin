import logging

from annoying.functions import get_object_or_None
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from django.urls import reverse

from astrobin.models import Image, UserProfile
from astrobin.stories import ACTSTREAM_VERB_COMMENTED_IMAGE, add_story
from astrobin_apps_equipment.models import (
    Accessory, Camera, EquipmentItemMarketplaceFeedback, EquipmentItemMarketplaceListing,
    EquipmentItemMarketplacePrivateConversation, Filter,
    Mount, Sensor, Software, Telescope,
)
from astrobin_apps_iotd.models import Iotd
from astrobin_apps_notifications.services import NotificationsService
from astrobin_apps_notifications.utils import build_notification_url, push_notification
from astrobin_apps_users.services import UserService
from common.services import AppRedirectionService
from common.services.mentions_service import MentionsService
from nested_comments.models import NestedComment

log = logging.getLogger(__name__)


class CommentNotificationsService:
    def __init__(self, comment):
        # type: (NestedComment) -> None
        self.comment = comment

    def extract_context(self):
        """
        Extracts the context of the comment, i.e. the object owner, the notification type, the mentions, the URL, etc.
        :return:
            - model_class: the model class of the object being commented
            - obj: the object being commented
            - object_owner: the owner of the object being commented
            - notification: the notification type
            - mentions: the mentions
            - url: the URL of the comment
            - target: the name of the object being commented
            - target_url: the URL of the object being commented 
        """

        model_class = self.comment.content_type.model_class()
        obj = self.comment.content_type.get_object_for_this_type(id=self.comment.object_id)
        object_owner = None
        notification = None
        mentions = MentionsService.get_mentions(self.comment.text)
        url = None
        target = str(self.comment.content_object)
        target_url = build_notification_url(
            settings.BASE_URL + self.comment.content_object.get_absolute_url(), self.comment.author
        ) if hasattr(self.comment.content_object, 'get_absolute_url') else None

        if model_class == Image:
            object_owner = obj.user
            notification = 'new_comment'
            url = settings.BASE_URL + self.comment.get_absolute_url()
        elif hasattr(model_class, 'edit_proposal_by'):
            object_owner = obj.edit_proposal_by
            notification = 'new_comment_to_edit_proposal'
            url = self.comment.get_absolute_url()
        elif model_class == Iotd:
            object_owner = obj.judge
            notification = 'new_comment_to_scheduled_iotd'
            url = AppRedirectionService.redirect(f'/iotd/judgement-queue#comments-{obj.pk}-{self.comment.pk}')
        elif model_class in (
                Sensor,
                Camera,
                Telescope,
                Filter,
                Mount,
                Accessory,
                Software
        ):
            object_owner = obj.created_by
            notification = 'new_comment_to_unapproved_equipment_item'
            url = AppRedirectionService.redirect(
                f'/equipment/explorer/{model_class.__name__.lower()}/{obj.pk}#c{self.comment.id}'
            )
        elif model_class == EquipmentItemMarketplacePrivateConversation:
            listing = obj.listing
            url = build_notification_url(
                settings.BASE_URL + obj.listing.get_absolute_url() + f'#c{self.comment.id}', self.comment.author
            )
            target = str(obj.listing)
            target_url = build_notification_url(
                settings.BASE_URL + obj.listing.get_absolute_url(), self.comment.author
            )
            if self.comment.author != listing.user:
                object_owner = obj.listing.user
                notification = 'new_comment_to_marketplace_private_conv'
            else:
                object_owner = obj.user
                notification = 'new_comment_to_marketplace_private_conv2'
        elif model_class == EquipmentItemMarketplaceListing:
            object_owner = obj.user
            notification = 'new_question_to_listing'
            url = build_notification_url(
                settings.BASE_URL + obj.get_absolute_url() + f'#c{self.comment.id}', self.comment.author
            )
            target = str(obj)
            target_url = build_notification_url(
                settings.BASE_URL + obj.get_absolute_url(), self.comment.author
            )
        elif model_class == EquipmentItemMarketplaceFeedback:
            if self.comment.author != obj.recipient:
                # We notify the recipient of the feedback
                object_owner = obj.recipient
                notification = 'comment-to-marketplace-feedback-received'
            else:
                # We notify the user who left the feedback
                object_owner = obj.user
                notification = 'comment-to-marketplace-feedback-left'
            url = build_notification_url(
                settings.BASE_URL + obj.get_absolute_url() + f'#c{self.comment.id}', self.comment.author
            )
            target = str(obj)
            target_url = build_notification_url(
                settings.BASE_URL + obj.get_absolute_url(), self.comment.author
            )

        return model_class, obj, object_owner, notification, mentions, url, target, target_url

    def send_notifications(self, force=False):
        if self.comment.pending_moderation and not force:
            return

        instance = self.comment
        model_class, obj, object_owner, notification, mentions, url, target, target_url = self.extract_context()

        if UserService(object_owner).shadow_bans(instance.author):
            log.info("Skipping notification for comment because %d shadow-bans %d" % (
                object_owner.pk, instance.author.pk))
            return

        exclude = MentionsService.get_mentioned_users_with_notification_enabled(mentions, 'new_comment_mention')

        if model_class == Image:
            if (force or not instance.pending_moderation) and not obj.is_wip:
                add_story(
                    instance.author,
                    verb=ACTSTREAM_VERB_COMMENTED_IMAGE,
                    action_object=instance,
                    target=obj,
                    like_count=obj.like_count,
                    bookmark_count=obj.bookmark_count,
                    comment_count=obj.comment_count + 1,
                )

        if instance.parent and \
                instance.parent.author != instance.author and \
                not instance.pending_moderation:
            recipients = [x for x in [instance.parent.author] if x not in exclude]
            if recipients:
                push_notification(
                    recipients, instance.author, 'new_comment_reply',
                    {
                        'url': build_notification_url(url, instance.author),
                        'user': instance.author.userprofile.get_display_name(),
                        'user_url': settings.BASE_URL + reverse(
                            'user_page', kwargs={'username': instance.author.username}
                        ),
                        'target': target,
                        'target_url': target_url,
                    }
                )

        if object_owner and notification:
            collaborators = [object_owner] + list(obj.collaborators.all()) if hasattr(obj, 'collaborators') else [
                object_owner]
            if instance.author not in collaborators and \
                    (instance.parent is None or instance.parent.author != object_owner) and \
                    not instance.pending_moderation:
                recipients = [x for x in collaborators if x not in exclude]
                if recipients:
                    push_notification(
                        recipients, instance.author, notification,
                        {
                            'url': build_notification_url(url, instance.author),
                            'user': instance.author.userprofile.get_display_name(),
                            'user_url': settings.BASE_URL + reverse(
                                'user_page', kwargs={'username': instance.author.username}
                            ),
                            'target': target,
                            'target_url': target_url,
                        }
                    )

    def send_mention_notifications(self, mentions=None):
        if not self.comment.pending_moderation:
            (
                _,
                _,
                _,
                _,
                mentions_,  # note the underscore: we don't want to override the `mentions` variable above.
                url,
                target,
                target_url
            ) = self.extract_context()

            if not mentions:
                mentions = mentions_

            for username in mentions:
                user = get_object_or_None(User, username=username)
                if not user:
                    try:
                        profile = get_object_or_None(UserProfile, real_name=username)
                        if profile:
                            user = profile.user
                    except UserProfile.MultipleObjectsReturned:
                        user = None
                if user:
                    push_notification(
                        [user], self.comment.author, 'new_comment_mention',
                        {
                            'url': build_notification_url(url, self.comment.author),
                            'user': self.comment.author.userprofile.get_display_name(),
                            'user_url': settings.BASE_URL + reverse(
                                'user_page', kwargs={'username': self.comment.author}
                            ),
                            'target': target,
                            'target_url': build_notification_url(target_url, self.comment.author),
                        }
                    )

    def send_approval_notification(self):
        if not self.comment.pending_moderation:
            push_notification([self.comment.author], None, 'comment_approved', {
                'url': build_notification_url(settings.BASE_URL + self.comment.get_absolute_url())
            })

    def send_moderation_required_notification(self):
        if self.comment.pending_moderation:
            ct = ContentType.objects.get_for_id(self.comment.content_type_id)
            if ct.model == 'image':
                image = self.comment.content_object
                push_notification([image.user], None, 'new_image_comment_moderation', {
                    'preheader': image.title,
                    'title': image.title,
                    'url': build_notification_url(
                        '%s%s?cid=%d#c%d' % (
                            settings.BASE_URL,
                            image.get_absolute_url(),
                            self.comment.pk,
                            self.comment.pk
                        ),
                        additional_query_args={'moderate-comment': 1})
                })

    @staticmethod
    def send_moderation_required_email_to_superuser():
        NotificationsService.email_superusers(
            'New comment needs moderation',
            '%s/admin/nested_comments/nestedcomment/?pending_moderation__exact=1' % settings.BASE_URL
        )

    @staticmethod
    def approve_comments(queryset: QuerySet, moderator: User) -> None:
        for comment in queryset:
            NestedComment.objects.filter(id=comment.id).update(pending_moderation=False, moderator=moderator)
            comment.refresh_from_db()
            service = CommentNotificationsService(comment)
            service.send_notifications(force=True)
            service.send_mention_notifications()
            service.send_approval_notification()
