import logging

from django.conf import settings
from django.urls import reverse

from astrobin.models import Image
from astrobin.stories import add_story
from astrobin_apps_notifications.utils import push_notification, build_notification_url
from astrobin_apps_users.services import UserService
from nested_comments.models import NestedComment

log = logging.getLogger('apps')


class CommentNotificationsService:
    def __init__(self, comment):
        # type: (NestedComment) -> None
        self.comment = comment

    def send_notifications(self):
        if self.comment.pending_moderation:
            return

        instance = self.comment

        model_class = instance.content_type.model_class()
        obj = instance.content_type.get_object_for_this_type(id=instance.object_id)
        url = settings.BASE_URL + instance.get_absolute_url()

        if model_class == Image:
            if UserService(obj.user).shadow_bans(instance.author):
                log.info("Skipping notification for comment because %d shadow-bans %d" % (
                    obj.user.pk, instance.author.pk))
                return

            if instance.parent and \
                    instance.parent.author != instance.author and \
                    not instance.pending_moderation:
                push_notification(
                    [instance.parent.author], instance.author, 'new_comment_reply',
                    {
                        'url': build_notification_url(url, instance.author),
                        'user': instance.author.userprofile.get_display_name(),
                        'user_url': settings.BASE_URL + reverse(
                            'user_page', kwargs={'username': instance.author.username}),
                    }
                )

            if instance.author != obj.user and \
                    (instance.parent is None or instance.parent.author != obj.user) and \
                    not instance.pending_moderation:
                push_notification(
                    [obj.user], instance.author, 'new_comment',
                    {
                        'url': build_notification_url(url, instance.author),
                        'user': instance.author.userprofile.get_display_name(),
                        'user_url': settings.BASE_URL + reverse(
                            'user_page', kwargs={'username': instance.author.username}),
                    }
                )

            if not instance.pending_moderation and not obj.is_wip:
                add_story(instance.author,
                          verb='VERB_COMMENTED_IMAGE',
                          action_object=instance,
                          target=obj)

    def send_approval_notification(self):
        if not self.comment.pending_moderation:
            push_notification([self.comment.author], None, 'comment_approved', {
                'url': build_notification_url(settings.BASE_URL + self.comment.get_absolute_url())
            })
