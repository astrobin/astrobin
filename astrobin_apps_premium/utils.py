from django.conf import settings

from subscription.models import UserSubscription


SUBSCRIPTION_NAMES = (
    'AstroBin Lite',
    'AstroBin Premium',
)

def premium_get_usersubscription(user):
    us = UserSubscription.objects.filter(
        user = user,
        subscription__name__in = SUBSCRIPTION_NAMES,
    )

    if us.count() > 0:
        us = us[0]
    else:
        return None

    return us


def premium_get_valid_usersubscription(user):
    us = UserSubscription.objects.filter(
        user = user,
        active = True,
        subscription__name__in = SUBSCRIPTION_NAMES,)

    if us.count() > 0:
        us = us[0]
    else:
        return None

    if not us.valid():
        return None

    return us

def premium_get_invalid_usersubscription(user):
    us = premium_get_usersubscription(user)
    if not us.valid():
        return us
    return None


def premium_used_percent(user):
    s = premium_get_valid_usersubscription(user)
    counter = user.userprofile.premium_counter
    percent = 100

    if s is None:
        # User is on Free, or their subscription is inactive, cancelled or
        # expired.
        percent = counter / float(settings.PREMIUM_MAX_IMAGES_FREE) * 100

    elif s.subscription.name == "AstroBin Lite":
        percent = counter / float(settings.PREMIUM_MAX_IMAGES_LITE) * 100

    elif s.subscription.name == "AstroBin Premium":
        percent = -1

    if percent > 100:
        percent = 100

    return percent


def premium_progress_class(p):
    if p < 90: return 'progress-success'
    if p > 97: return 'progress-danger'
    return 'progress-warning'


def premium_user_has_subscription(user):
    us = premium_get_usersubscription(user)
    return us is not None


def premium_user_has_valid_subscription(user):
    us = premium_get_valid_usersubscription(user)
    return us is not None


def premium_user_has_invalid_subscription(user):
    us = premium_get_invalid_usersubscription(user)
    return us is not None
