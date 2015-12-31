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
            subscription__name = 'AstroBin Premium',
            cancelled = False
        )

        if us.count() == 0:
            return False

        us = us[0]
        return us.valid() and not us.expired()

    return False


@register.filter
def is_lite(user):
    if user.is_authenticated():
        us = UserSubscription.active_objects.filter(
            user = user,
            subscription__name = 'AstroBin Lite',
            cancelled = False
        )

        if us.count() == 0:
            return False

        us = us[0]
        return us.valid() and not us.expired()

    return False


@register.filter
def is_free(user):
    return not (is_lite(user) or is_premium(user))
