import re
from typing import Optional, List

from annoying.functions import get_object_or_None
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from notification.models import NoticeSetting


class MentionsService(object):
    @staticmethod
    def get_mentions(text):
        # type: (str) -> list[str]

        if not text:
            return []

        regex = r'\[url=.*?\/users\/(.*?)\/\]@.*?\[\/url\]|\[quote="(.*?)"\].*?\[\/quote\]'
        matches = re.finditer(regex, text, re.MULTILINE)
        mentions = []

        for matchNum, match in enumerate(matches, start=1):
            for group in match.groups():
                if group is not None:
                    mentions.append(group)

        return list(set(mentions))

    @staticmethod
    def get_mentioned_users_with_notification_enabled(mentions, notice_type):
        # type: (list[str], str) -> list[User]

        mentioned_user_with_notification_enabled: List[User] = []
        mention: str
        for mention in mentions:
            user: Optional[User] = get_object_or_None(User, username=mention)
            if not user:
                try:
                    user = get_object_or_None(User, userprofile__real_name=mention)
                except MultipleObjectsReturned:
                    user = None
            if user:
                gets_mention_notifications: bool = NoticeSetting.objects.filter(
                    user=user,
                    notice_type__label=notice_type,
                    send=True).exists()
                if gets_mention_notifications:
                    mentioned_user_with_notification_enabled.append(user)

        return mentioned_user_with_notification_enabled
