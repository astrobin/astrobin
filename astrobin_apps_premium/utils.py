import sys

from django.conf import settings
from subscription.models import UserSubscription

SUBSCRIPTION_NAMES = (
    'AstroBin Lite',
    'AstroBin Premium',

    'AstroBin Lite 2020+',
    'AstroBin Premium 2020+',
    'AstroBin Ultimate 2020+',

    'AstroBin Lite (autorenew)',
    'AstroBin Premium (autorenew)',

    'AstroBin Premium 20% discount',
    'AstroBin Premium 30% discount',
    'AstroBin Premium 40% discount',
    'AstroBin Premium 50% discount',
)


def _compareValidity(a, b):
    return a.valid() - b.valid()


def _compareNames(a, b):
    """
    This function is used to determin the "weight" of each Premium subscription. When a user has multiple, only the
    heaviest one gets considered throughout the website.
    :param a: left operand.
    :param b: right operand.
    :return: a negative number if the left operand is heavier than thee left, 0 if equal, a positive number otherwise.
    """
    key = {
        "AstroBin Lite (autorenew)": 0,
        "AstroBin Lite": 1,
        "AstroBin Lite 2020+": 2,
        "AstroBin Premium (autorenew)": 3,
        "AstroBin Premium": 4,
        'AstroBin Premium 20% discount': 5,
        'AstroBin Premium 30% discount': 6,
        'AstroBin Premium 40% discount': 7,
        'AstroBin Premium 50% discount': 8,
        "AstroBin Premium 2020+": 9,
        "AstroBin Ultimate 2020+": 10
    }

    return key[b.subscription.name] - key[a.subscription.name]


def premium_get_usersubscription(user):
    us = UserSubscription.objects.filter(
        user=user,
        subscription__name__in=SUBSCRIPTION_NAMES,
    )

    if us.count() == 0:
        return None

    if us.count() == 1:
        return us[0]

    return sorted(list(us), cmp=_compareNames)[0]


def premium_get_valid_usersubscription(user):
    us = [obj for obj in UserSubscription.objects.filter(
        user__username=user.username,
        subscription__name__in=SUBSCRIPTION_NAMES,
        active=True,
    ) if obj.valid()]

    if len(us) == 0:
        return None

    if len(us) == 1:
        return us[0]

    sortedByName = sorted(us, cmp=_compareNames)
    sortedByValidity = sorted(sortedByName, cmp=_compareValidity)

    return sortedByName[0]


def premium_get_invalid_usersubscription(user):
    us = [obj for obj in UserSubscription.objects.filter(
        user__username=user.username,
        subscription__name__in=SUBSCRIPTION_NAMES,
        active=True,
    ) if not obj.valid()]

    if len(us) == 0:
        return None

    if len(us) == 1:
        return us[0]

    sortedByName = sorted(us, cmp=_compareNames)
    sortedByValidity = sorted(sortedByName, cmp=_compareValidity)

    return sortedByName[0]


def premium_used_percent(user):
    s = premium_get_valid_usersubscription(user)
    counter = user.userprofile.premium_counter
    percent = 100

    if s is None:
        # User is on Free, or their subscription is inactive, or expired.
        percent = counter / float(settings.PREMIUM_MAX_IMAGES_FREE) * 100

    elif s.subscription.group.name == "astrobin_lite":
        percent = counter / float(settings.PREMIUM_MAX_IMAGES_LITE) * 100

    elif s.subscription.group.name == "astrobin_premium":
        # Premium gets unlimited uploads.
        percent = -1

    elif s.subscription.group.name == "astrobin_lite_2020":
        percent = counter / float(settings.PREMIUM_MAX_IMAGES_LITE_2020) * 100

    elif s.subscription.group.name == "astrobin_premium_2020":
        percent = -1

    elif s.subscription.group.name == "astrobin_ultimate_2020":
        # Ultimate 2020 gets unlimited uploads.
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
    return not premium_user_has_valid_subscription(user) and us is not None


def premium_get_max_allowed_image_size(user):
    s = premium_get_valid_usersubscription(user)

    if s is None:
        return settings.PREMIUM_MAX_IMAGE_SIZE_FREE_2020

    if s.subscription.group.name == "astrobin_lite":
        return sys.maxsize

    if s.subscription.group.name == "astrobin_premium":
        return sys.maxsize

    if s.subscription.group.name == "astrobin_lite_2020":
        return settings.PREMIUM_MAX_IMAGE_SIZE_LITE_2020

    if s.subscription.group.name == "astrobin_premium_2020":
        return settings.PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020

    if s.subscription.group.name == "astrobin_ultimate_2020":
        return sys.maxsize

    return 0


def premium_get_max_allowed_revisions(user):
    s = premium_get_valid_usersubscription(user)

    if s is None:
        return settings.PREMIUM_MAX_REVISIONS_FREE_2020

    if s.subscription.group.name == "astrobin_lite":
        return sys.maxsize

    if s.subscription.group.name == "astrobin_premium":
        return sys.maxsize

    if s.subscription.group.name == "astrobin_lite_2020":
        return settings.PREMIUM_MAX_REVISIONS_LITE_2020

    if s.subscription.group.name == "astrobin_premium_2020":
        return settings.PREMIUM_MAX_REVISIONS_PREMIUM_2020

    if s.subscription.group.name == "astrobin_ultimate_2020":
        return sys.maxsize

    return 0
