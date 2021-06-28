import re

from annoying.functions import get_object_or_None
from django.contrib.auth.models import User
from notification.models import NoticeSetting


class MentionsService(object):
    @staticmethod
    def get_mentions(text):
        # type: (unicode) -> list[unicode]
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
        # type: (List[User]) -> List[User]
        mentioned_user_with_notification_enabled = []  # type: List[User]
        for mention in mentions:  # type: unicode
            user = get_object_or_None(User, username=mention)  # type: Optional[User]
            if not user:
                user = get_object_or_None(User, userprofile__real_name=mention)
            if user:
                gets_mention_notifications = NoticeSetting.objects.filter(
                    user=user,
                    notice_type__label=notice_type,
                    send=True).exists()  # type: bool
                if gets_mention_notifications:
                    mentioned_user_with_notification_enabled.append(user)

        return mentioned_user_with_notification_enabled
