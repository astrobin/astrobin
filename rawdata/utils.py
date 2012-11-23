from subscription.models import UserSubscription

from .models import RawImage

def user_used_bytes(user):
    sizes = RawImage.objects\
        .filter(user = user)\
        .values_list('size', flat = True)
    return sum(sizes)


def user_used_percent(user):
    b = user_used_bytes(user)
    limit = user_byte_limit(user)
    return b * 100 / limit


def user_progress_class(user):
    p = user_used_percent(user)
    if p < 90: return 'progress-success'
    if p > 97: return 'progress-danger'
    return 'progress-warning'


def user_is_over_limit(user):
    return user_used_percent(user) >= 100

def user_get_subscription(user):
    if not user.is_authenticated():
        raise UserSubscription.DoesNotExist

    return UserSubscription.objects.get(user = user)


def user_has_subscription(user):
    try:
        user_get_subscription(user)
    except UserSubscription.DoesNotExist:
        return False

    return True
 

def user_has_active_subscription(user):
    try:
        us = user_get_subscription(user)
    except UserSubscription.DoesNotExist:
        return False

    return us.active and not us.cancelled and not us.expired()

def user_has_inactive_subscription(user):
    try:
        us = user_get_subscription(user)
    except UserSubscription.DoesNotExist:
        return False

    return not us.active or us.cancelled or us.expired()


def subscription_byte_limit(subscription):
    GB = 1024*1024*1024
    if subscription.group.name == 'rawdata-25':
        return 25*GB
    if subscription.group.name == 'rawdata-50':
        return 50*GB
    if subscription.group.name == 'rawdata-100':
        return 100*GB

    return 0
   

def user_byte_limit(user):
    try:
        us = user_get_subscription(user)
    except UserSubscription.DoesNotExist:
        return 0

    return subscription_byte_limit(us.subscription)
