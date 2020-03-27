from subscription.models import UserSubscription

SUBSCRIPTION_NAMES = (
    'AstroBin Donor Coffee Monthly',
    'AstroBin Donor Snack Monthly',
    'AstroBin Donor Pizza Monthly',
    'AstroBin Donor Movie Monthly',
    'AstroBin Donor Dinner Monthly',

    'AstroBin Donor Coffee Yearly',
    'AstroBin Donor Snack Yearly',
    'AstroBin Donor Pizza Yearly',
    'AstroBin Donor Movie Yearly',
    'AstroBin Donor Dinner Yearly',

    'AstroBin Donor Bronze Monthly',
    'AstroBin Donor Silver Monthly',
    'AstroBin Donor Gold Monthly',
    'AstroBin Donor Platinum Monthly',

    'AstroBin Donor Bronze Yearly',
    'AstroBin Donor Silver Yearly',
    'AstroBin Donor Gold Yearly',
    'AstroBin Donor Platinum Yearly',
)


def donations_user_get_subscription(user):
    try:
        return UserSubscription.objects.get(user = user, subscription__name__in = SUBSCRIPTION_NAMES)
    except UserSubscription.DoesNotExist:
        return None
    except UserSubscription.MultipleObjectsReturned:
        return UserSubscription.objects.filter(user = user, subscription__name__in = SUBSCRIPTION_NAMES)[0]


def donations_user_get_active_subscription(user):
    try:
        us = UserSubscription.objects.get(user = user, subscription__name__in = SUBSCRIPTION_NAMES, active = True, cancelled = False)
    except UserSubscription.DoesNotExist:
        return None
    except UserSubscription.MultipleObjectsReturned:
        us = UserSubscription.objects.filter(user = user, subscription__name__in = SUBSCRIPTION_NAMES, active = True, cancelled = False)[0]

    if us.expired():
        return None

    return us


def donations_user_has_subscription(user):
    try:
        donations_user_get_subscription(user)
    except UserSubscription.DoesNotExist:
        return False

    return True


def donations_user_has_valid_subscription(user):
    try:
        us = donations_user_get_active_subscription(user)
    except UserSubscription.DoesNotExist:
        return False

    if us:
        return us.active and not us.cancelled and not us.expired()

    False

def donations_user_has_inactive_subscription(user):
    active = donations_user_has_valid_subscription(user)
    if active:
        return False

    try:
        us = donations_user_get_subscription(user)
    except UserSubscription.DoesNotExist:
        return False

    return not us.active or us.cancelled or us.expired()
