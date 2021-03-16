# Django
from django.db.models import Q

# Third party apps
from pybb.permissions import DefaultPermissionHandler

# AstroBin apps
from astrobin_apps_groups.models import Group


class CustomForumPermissions(DefaultPermissionHandler):
    # Disable forum polls
    def may_create_poll(self, user):
        return False


    def may_view_forum(self, user, forum):
        may = super(CustomForumPermissions, self).may_view_forum(user, forum)

        try:
            if forum.group is not None:
                if user.is_authenticated():
                    return may and (
                        forum.group.public or \
                        user == forum.group.owner or \
                        user in forum.group.members.all())
                else:
                    return may and forum.group.public
        except Group.DoesNotExist:
            pass

        return may


    def filter_forums(self, user, qs):
        f = super(CustomForumPermissions, self).filter_forums(user, qs)

        if user.is_authenticated():
            f = f.filter(
                Q(group = None) |
                Q(group__owner = user) |
                Q(group__members = user)).distinct()
        else:
            f = f.filter(group = None)

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
            if topic.forum.group and user.is_authenticated():
                may = user == topic.forum.group.owner or \
                      user in topic.forum.group.members.all() or \
                      user in topic.subscribers.all()
        except Group.DoesNotExist:
            pass

        return may


    def filter_topics(self, user, qs):
        f = super(CustomForumPermissions, self).filter_topics(user, qs)

        if user.is_authenticated():
            f = f.filter(
                Q(forum__group = None) |
                Q(forum__group__owner = user) |
                Q(forum__group__members = user)).distinct()
        else:
            f = f.filter(forum__group = None)

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
