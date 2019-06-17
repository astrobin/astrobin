# Python

# Django
from django.template import Library

# This app
from astrobin_apps_premium.utils import premium_get_valid_usersubscription

# Third party

register = Library()


@register.inclusion_tag('astrobin_apps_premium/inclusion_tags/premium_badge.html')
def premium_badge(user, size='large'):
    return {
        'user': user,
        'size': size,
    }


@register.filter
def is_premium(user):
    if user.is_authenticated():
        userSubscription = premium_get_valid_usersubscription(user)
        if userSubscription:
            return 'AstroBin Premium' in userSubscription.subscription.name
    return False


@register.filter
def is_lite(user):
    if user.is_authenticated():
        userSubscription = premium_get_valid_usersubscription(user)
        if userSubscription:
            return 'AstroBin Lite' in userSubscription.subscription.name
    return False


@register.filter
def is_free(user):
    return not (is_lite(user) or is_premium(user))
