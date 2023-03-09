import datetime

from django.db.models import Q
from pybb.permissions import DefaultPermissionHandler

from astrobin_apps_groups.models import Group
from astrobin_apps_premium.services.premium_service import PremiumService


class CustomForumPermissions(DefaultPermissionHandler):
    def may_view_forum(self, user, forum):
        may = super(CustomForumPermissions, self).may_view_forum(user, forum)

        try:
            if forum.group is not None:
                if user.is_authenticated:
                    return may and (
                            forum.group.public or
                            user == forum.group.owner or
                            user in forum.group.members.all())
                else:
                    return may and forum.group.public
        except Group.DoesNotExist:
            pass

        return may

    def filter_posts(self, user, qs):
        f = super(CustomForumPermissions, self).filter_posts(user, qs)

        if user.is_authenticated:
            f = f.filter(
                Q(topic__forum__group=None) |
                Q(topic__forum__group__public=True) |
                Q(topic__forum__group__owner=user) |
                Q(topic__forum__group__members=user)
            ).distinct()
        else:
            f = f.filter(Q(topic__forum__group=None) | Q(topic__forum__group__public=True))

        return f

    def filter_forums(self, user, qs):
        f = super(CustomForumPermissions, self).filter_forums(user, qs)

        if user.is_authenticated:
            f = f.filter(
                Q(group=None) |
                Q(group__owner=user) |
                Q(group__members=user)).distinct()
        else:
            f = f.filter(group=None)

        return f

    def may_view_topic(self, user, topic):
        may = super(CustomForumPermissions, self).may_view_topic(user, topic)

        if user.is_superuser:
            return True

        if not user.is_superuser and (topic.forum.hidden or topic.forum.category.hidden):
            return False  # only superuser may see hidden forum / category

        if topic.on_moderation and topic.user == user:
            return True

        try:
            if topic.forum.group:
                if user.is_authenticated:
                    may = (
                            topic.forum.group.public or
                            user == topic.forum.group.owner or
                            user in topic.forum.group.members.all() or
                            user in topic.subscribers.all()
                    )
                else:
                    may = topic.forum.group.public
        except Group.DoesNotExist:
            pass

        return may

    def filter_topics(self, user, qs):
        f = super(CustomForumPermissions, self).filter_topics(user, qs)

        if user.is_authenticated:
            f = f.filter(
                Q(forum__group=None) |
                Q(forum__group__public=True) |
                Q(forum__group__owner=user) |
                Q(forum__group__members=user)).distinct()
        else:
            f = f.filter(Q(forum__group=None) | Q(forum__group__public=True))

        return f

    def may_create_topic(self, user, forum):
        may = super(CustomForumPermissions, self).may_create_topic(user, forum)

        try:
            if forum.group is not None:
                return may and (
                        user == forum.group.owner or
                        user in forum.group.members.all())
        except Group.DoesNotExist:
            pass

        return may

    def may_create_post(self, user, topic):
        may = super(CustomForumPermissions, self).may_create_post(user, topic)
        return may and self.may_create_topic(user, topic.forum)

    def may_edit_post(self, user, post):
        if user.is_superuser:
            return True

        if post.user != user:
            return False

        valid_subscription = PremiumService(user).get_valid_usersubscription()

        return (
                self.may_moderate_post(user, post) or
                post.created >= datetime.datetime.now() - datetime.timedelta(days=1) or
                PremiumService.is_any_paid_subscription(valid_subscription) or
                PremiumService.has_expired_paid_subscription(user)
        )
