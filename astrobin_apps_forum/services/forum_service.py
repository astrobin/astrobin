import logging
from datetime import timedelta
from typing import Union

from annoying.functions import get_object_or_None
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache.utils import make_template_fragment_key
from django.db.models import QuerySet
from django.urls import reverse
from django.utils import timezone
from pybb.models import Forum, ForumReadTracker, Post, Topic, TopicReadTracker

from astrobin_apps_equipment.models import Accessory, Camera, EquipmentItem, Filter, Mount, Sensor, Software, Telescope
from astrobin_apps_equipment.services import EquipmentItemService
from astrobin_apps_forum.models import TopicRedirect
from astrobin_apps_notifications.utils import build_notification_url, push_notification
from common.services import AppRedirectionService

log = logging.getLogger(__name__)


class ForumService:
    forum = None

    def __init__(self, forum: Forum):
        self.forum = forum

    def get_equipment_item(self):
        if self.forum.category.slug != 'equipment-forums':
            return None

        for ModelClass in (
                Sensor,
                Camera,
                Telescope,
                Mount,
                Filter,
                Accessory,
                Software
        ):
            item: ModelClass = get_object_or_None(ModelClass, forum=self.forum)
            if item:
                return item

        return None

    @staticmethod
    def notify_equipment_users(topic: Topic) -> None:
        if topic.created < timezone.now() - timedelta(days=7):
            log.debug(f"Topic {topic.id} is too old to send the 'new_topic_for_equipment_you_use' notification")
            return

        item: EquipmentItem = ForumService(topic.forum).get_equipment_item()

        if not item:
            log.error(f"Topic {topic.id} is not in an equipment forum")
            return

        users: QuerySet = EquipmentItemService(item).get_users().exclude(pk=topic.user.pk)

        if users.exists():
            log.debug(f"Found {users.count()} users for equipment item {item}")
            push_notification(
                list(users),
                topic.user,
                'new_topic_for_equipment_you_use',
                {
                    'user': topic.user.userprofile.get_display_name(),
                    'user_url': settings.BASE_URL + reverse('user_page', kwargs={'username': topic.user}),
                    'topic_url': build_notification_url(settings.BASE_URL + topic.get_absolute_url(), topic.user),
                    'preheader': topic.name,
                    'topic_name': topic.name,
                    'item': item,
                    'item_url': build_notification_url(
                        AppRedirectionService.redirect(
                            f'/equipment/explorer/{item.klass.lower()}/{item.pk}'
                        )
                    ),
                }
            )
        else:
            log.debug(f"No users found for equipment item {item}")

        followers = EquipmentItemService(item).get_followers().exclude(pk=topic.user.pk)
        user_ids = users.values_list('id', flat=True)
        if followers.exists():
            for follower in followers:
                if follower.id not in user_ids:
                    push_notification(
                        [follower],
                        topic.user,
                        'new_topic_for_equipment_you_follow',
                        {
                            'user': topic.user.userprofile.get_display_name(),
                            'user_url': settings.BASE_URL + reverse('user_page', kwargs={'username': topic.user}),
                            'topic_url': build_notification_url(settings.BASE_URL + topic.get_absolute_url(), topic.user),
                            'preheader': topic.name,
                            'topic_name': topic.name,
                            'item': item,
                            'item_url': build_notification_url(
                                AppRedirectionService.redirect(
                                    f'/equipment/explorer/{item.klass.lower()}/{item.pk}'
                                )
                            ),
                        }
                    )

    @staticmethod
    def get_topic_first_unread(topic: Topic, user: User) -> Union[Post, None]:
        if not user.is_authenticated:
            return None

        read_dates = []

        try:
            read_dates.append(TopicReadTracker.objects.get(user=user, topic=topic).time_stamp)
        except TopicReadTracker.DoesNotExist:
            pass

        try:
            read_dates.append(ForumReadTracker.objects.get(user=user, forum=topic.forum).time_stamp)
        except ForumReadTracker.DoesNotExist:
            pass

        read_date = read_dates and max(read_dates)

        if read_date:
            try:
                return topic.posts.filter(created__gt=read_date).order_by('created', 'id')[0]
            except IndexError:
                return None

        return None

    @staticmethod
    def create_topic_redirect(new_category_slug:str , new_forum_slug:str , new_slug: str, topic: Topic):
        # Prevent loops.
        TopicRedirect.objects.filter(
            category_slug=new_category_slug,
            forum_slug=new_forum_slug,
            slug=new_slug,
            topic=topic,
        ).delete()

        TopicRedirect.objects.get_or_create(
            category_slug=topic.forum.category.slug,
            forum_slug=topic.forum.slug,
            slug=topic.slug,
            topic=topic,
        )

    @staticmethod
    def home_page_latest_from_forum_cache_key(user: User):
        return make_template_fragment_key(
            'home_page_latest_from_forums',
            (user.pk, user.userprofile.language)
        )
