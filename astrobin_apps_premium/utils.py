from django.conf import settings

from subscription.models import UserSubscription


SUBSCRIPTION_NAMES = (
    'AstroBin Lite',
    'AstroBin Premium',
)


def premium_get_subscription(user):
    us = UserSubscription.objects.filter(
        user = user,
        subscription__name__in = SUBSCRIPTION_NAMES,
        active = True,
        cancelled = False,
    )

    if us.count() > 0:
        us = us[0]
    else:
        return None

    if us.expired():
        return None

    return us.subscription

def premium_used_percent(user):
    s = premium_get_subscription(user)
    counter = user.userprofile.premium_counter

    if s is None:
        # User is on Free, or their subscription is inactive, cancelled or
        # expired.
        return counter / settings.PREMIUM_MAX_IMAGES_FREE * 100

    elif s.name == "AstroBin Lite":
        return counter / settings.PREMIUM_MAX_IMAGES_LITE * 100

    elif s.name == "AstroBin Premium":
        return -1

    return 100 # Should not happen.


def premium_progress_class(p):
    if p < 90: return 'progress-success'
    if p > 97: return 'progress-danger'
    return 'progress-warning'
