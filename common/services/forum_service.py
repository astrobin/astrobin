from typing import Union

from django.contrib.auth.models import User
from pybb.models import Topic, TopicReadTracker, ForumReadTracker, Post


class ForumService:
    @staticmethod
    def get_topic_first_unread(topic, user):
        # type: (Topic, User) -> Union[Post, None]

        if not user.is_authenticated():
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
