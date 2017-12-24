# Python
import urllib

# Django
from django.conf import settings
from django.db.models import Q
from django.template import Library, Node

# Third party
from subscription.models import Subscription, UserSubscription


register = Library()


@register.inclusion_tag('astrobin_apps_premium/inclusion_tags/premium_badge.html')
def premium_badge(user, size = 'large'):
    return {
        'user': user,
        'size': size,
    }


@register.filter
def is_premium(user):
    if user.is_authenticated():
        us = UserSubscription.active_objects.filter(
            user = user,
            subscription__group__name = 'astrobin_premium')

        if us.count() == 0:
            return False

        return us[0].valid()

    return False


@register.filter
def is_lite(user):
    if user.is_authenticated():
        us = UserSubscription.active_objects.filter(
            user = user,
            subscription__group__name = 'astrobin_lite')

        if us.count() == 0:
            return False

        return us[0].valid()

    return False


@register.filter
def is_free(user):
    return not (is_lite(user) or is_premium(user))
