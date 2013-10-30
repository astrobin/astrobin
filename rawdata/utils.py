from subscription.models import UserSubscription

from .models import RawImage


SUBSCRIPTION_NAMES = (
    'Meteor',
    'Luna',
    'Sol',
    'Galaxia',
)


def user_used_bytes(user):
    sizes = RawImage.objects\
        .filter(user = user)\
        .values_list('size', flat = True)
    return sum(sizes)


def user_used_percent(user):
    b = user_used_bytes(user)
    limit = user_byte_limit(user)
    return b * 100 / limit if limit > 0 else 100


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

    return UserSubscription.objects.get(user = user, subscription__name__in = SUBSCRIPTION_NAMES)


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

    # Used in the unit tests
    if subscription.group.name == 'rawdata-empty':
        return 0

    if subscription.group.name == 'rawdata-meteor':
        return 5*GB
    if subscription.group.name == 'rawdata-luna':
        return 100*GB
    if subscription.group.name == 'rawdata-sol':
        return 200*GB
    if subscription.group.name == 'rawdata-galaxia':
        return 500*GB

    return 0


def user_byte_limit(user):
    try:
        us = user_get_subscription(user)
    except UserSubscription.DoesNotExist:
        return 0

    return subscription_byte_limit(us.subscription)

def supported_raw_formats():
    return [
        "fit", "fits", "fts",

        "3fr",
        "ari", "arw",
        "bay",
        "crw", "cr2", "cap",
        "dcs", "dcr", "dng", "drf",
        "eip", "erf",
        "fff",
        "iiq",
        "k25", "kdc",
        "mef", "mos", "mrw",
        "nef", "nrw",
        "obm", "orf",
        "pef", "ptx", "pxn",
        "r3d", "raf", "raw", "rwl", "rw2", "rwz",
        "sr2", "srf", "srw",
        "x3f",
    ]


def md5_for_file(f, block_size=2**20):
    import hashlib
    md5 = hashlib.md5()
    f.seek(0)
    while True:
        data = f.read(block_size)
        if not data:
            break
        md5.update(data)
    return md5.hexdigest()

