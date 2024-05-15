from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.template import Library
from subscription.models import UserSubscription

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
def has_access_to_premium_group_features(user_subscription: UserSubscription) -> bool:
    return utils.has_access_to_premium_group_features(user_subscription)


@register.filter
def groups_for_user(user: User) -> QuerySet:
    if user.is_authenticated:
        return user.joined_group_set.all()
    return Group.objects.none()


@register.filter
def is_in_group(user: User, group_name: str) -> bool:
    return user.joined_group_set.filter(name=group_name).exists()
