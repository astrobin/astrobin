from django.contrib.auth.models import User
from django.template import Library

from astrobin_apps_groups import utils
from astrobin_apps_groups.models import Group

register = Library()


@register.filter
def count_images_in_group(user, group):
    # type: (User, Group) -> int
    return group.images.filter(user=user).count()


@register.filter
def count_forum_posts_in_group(user, group):
    # type: (User, Group) -> int
    return group.forum.posts.filter(user=user).count()


@register.filter
def has_access_to_premium_group_features(user):
    # type: (User) -> bool
    return utils.has_access_to_premium_group_features(user)
