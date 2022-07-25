from typing import Union

from annoying.functions import get_object_or_None
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.urls import reverse
from pybb.models import Forum, ForumReadTracker, Post, Topic, TopicReadTracker

from astrobin_apps_equipment.models import Accessory, Camera, EquipmentItem, Filter, Mount, Sensor, Software, Telescope
from astrobin_apps_equipment.services import EquipmentItemService
from astrobin_apps_notifications.utils import build_notification_url, push_notification
from common.services import AppRedirectionService


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

    def notify_equipment_users(topic: Topic) -> None:
        item: EquipmentItem = ForumService(topic.forum).get_equipment_item()

        if not item:
            return

        recipients: QuerySet = EquipmentItemService(item).get_users()

        if recipients.exists():
            push_notification(
                list(recipients),
                topic.user,
                'new_topic_for_equipment_you_use',
                {
                    'user': topic.user.userprofile.get_display_name(),
                    'user_url': settings.BASE_URL + reverse('user_page', kwargs={'username': topic.user}),
                    'topic_url': build_notification_url(settings.BASE_URL + topic.get_absolute_url(), topic.user),
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
