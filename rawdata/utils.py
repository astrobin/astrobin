from subscription.models import UserSubscription

from .models import RawImage


SUBSCRIPTION_NAMES = (
    'Atom',
    'Meteor',
    'Luna',
    'Sol',
    'Galaxia',

    'test_subscription',
    'test_subscription_empty',
)


def rawdata_user_used_bytes(user):
    sizes = RawImage.objects\
        .filter(user = user)\
        .values_list('size', flat = True)
    return sum(sizes)


def rawdata_user_used_percent(user):
    b = rawdata_user_used_bytes(user)
    limit = rawdata_user_byte_limit(user)
    return b * 100 / limit if limit > 0 else 100


def rawdata_user_progress_class(user):
    p = rawdata_user_used_percent(user)
    if p < 90: return 'progress-success'
    if p > 97: return 'progress-danger'
    return 'progress-warning'


def rawdata_user_is_over_limit(user):
    return rawdata_user_used_percent(user) >= 100

def rawdata_user_get_subscription(user):
    if not user.is_authenticated():
        raise UserSubscription.DoesNotExist

    try:
        return UserSubscription.objects.get(user = user, subscription__name__in = SUBSCRIPTION_NAMES)
    except UserSubscription.MultipleObjectsReturned:
        return UserSubscription.objects.filter(user = user, subscription__name__in = SUBSCRIPTION_NAMES)[0]


def rawdata_user_get_valid_subscription(user):
    if not user.is_authenticated():
        raise UserSubscription.DoesNotExist

    us = UserSubscription.active_objects.filter(user = user, subscription__name__in = SUBSCRIPTION_NAMES)
    if us.count() == 0 or not us[0].valid():
        raise UserSubscription.DoesNotExist

    return us[0]


def rawdata_user_has_subscription(user):
    try:
        rawdata_user_get_subscription(user)
    except UserSubscription.DoesNotExist:
        return False

    return True


def rawdata_user_has_valid_subscription(user):
    try:
        us = rawdata_user_get_valid_subscription(user)
    except UserSubscription.DoesNotExist:
        return False

    return True

def rawdata_user_has_invalid_subscription(user):
    valid = rawdata_user_has_valid_subscription(user)
    if valid:
        return False

    try:
        us = rawdata_user_get_subscription(user)
    except UserSubscription.DoesNotExist:
        return False

    return not us.valid()


def rawdata_subscription_byte_limit(subscription):
    GB = 1024*1024*1024

    # Used in the unit tests
    if subscription.group.name == 'rawdata-empty':
        return 0
    if subscription.group.name == 'rawdata-test':
        return 5*GB

    if subscription.group.name == 'rawdata-atom':
        return 0.5*GB
    if subscription.group.name == 'rawdata-meteor':
        return 5*GB
    if subscription.group.name == 'rawdata-luna':
        return 100*GB
    if subscription.group.name == 'rawdata-sol':
        return 200*GB
    if subscription.group.name == 'rawdata-galaxia':
        return 500*GB

    if subscription.group.name == 'rawdata-atom-2020':
        return 5 * GB
    if subscription.group.name == 'rawdata-meteor-2020':
        return 50 * GB
    if subscription.group.name == 'rawdata-luna-2020':
        return 250 * GB
    if subscription.group.name == 'rawdata-sol-2020':
        return 500 * GB
    if subscription.group.name == 'rawdata-galaxia-2020':
        return 1000 * GB

    return 0


def rawdata_user_byte_limit(user):
    try:
        us = rawdata_user_get_valid_subscription(user)
    except UserSubscription.DoesNotExist:
        return 0

    return rawdata_subscription_byte_limit(us.subscription)

def rawdata_supported_raw_formats():
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
