# Python
import datetime
import sys

# Third party
import pytz
# Django
from django.conf import settings
from django.contrib.gis.geoip2 import GeoIP2
from django.db.models import Count
from django.utils import timezone


def unique_items(l):
    found = []
    for i in l:
        if i not in found:
            found.append(i)
    return found


ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
def base26_encode(num, alphabet=ALPHABET):
    """Encode a number in Base X

    `num`: The number to encode
    `alphabet`: The alphabet to use for encoding
    """
    if (num == 0):
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)

def base26_decode(string, alphabet=ALPHABET):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for encoding
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num


# need to translate to a non-naive timezone, even if timezone ==
# settings.TIME_ZONE, so we can compare two dates
def to_user_timezone(date, profile):
    if date is None:
        return None

    timezone = profile.timezone if profile.timezone else settings.TIME_ZONE
    return date.replace(tzinfo=pytz.timezone(settings.TIME_ZONE))\
        .astimezone(pytz.timezone(timezone))


def to_system_timezone(date, profile):
    if date is None:
        return None

    timezone = profile.timezone if profile.timezone else settings.TIME_ZONE
    return date.replace(tzinfo=pytz.timezone(timezone))\
        .astimezone(pytz.timezone(settings.TIME_ZONE))


def now_timezone():
    return datetime.now()\
        .replace(tzinfo=pytz.timezone(settings.TIME_ZONE))\
        .astimezone(pytz.timezone(settings.TIME_ZONE))


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_client_country_code(request):
    try:
        DEBUG_COUNTRY = request.GET.get('DEBUG_COUNTRY', None)
        if DEBUG_COUNTRY is not None:
            return DEBUG_COUNTRY
    except AttributeError:
        pass

    geoip2 = GeoIP2()

    try:
        return geoip2.country_code(get_client_ip(request))
    except:
        return "UNKNOWN"


#################################
# TODO: move to affiliation app #
#################################
def user_is_producer(user):
    is_producer = False
    if user:
        is_producer = user.groups.filter(name = 'Producers').count() > 0
    return is_producer


def user_is_retailer(user):
    if user:
        return user.groups.filter(name = 'Retailers').count() > 0
    return False 

def user_is_paying(user):
    if user:
        return user.groups.filter(name = 'Paying').count() > 0
    return False 


def affiliate_limit(user):
    if not user:
        return 0

    if user.groups.filter(name = 'affiliate-1'):
        return 1
    if user.groups.filter(name = 'affiliate-10'):
        return 10
    if user.groups.filter(name = 'affiliate-50'):
        return 50
    if user.groups.filter(name = 'affiliate-100'):
        return 100
    if user.groups.filter(name = 'affiliate-inf'):
        return sys.maxint

    return 0


def retailer_affiliate_limit(user):
    if not user:
        return 0

    if user.groups.filter(name = 'retailer-affiliate-1'):
        return 1
    if user.groups.filter(name = 'retailer-affiliate-10'):
        return 10
    if user.groups.filter(name = 'retailer-affiliate-50'):
        return 50
    if user.groups.filter(name = 'retailer-affiliate-100'):
        return 100
    if user.groups.filter(name = 'retailer-affiliate-inf'):
        return sys.maxint

    return 0


def inactive_accounts():
    """Gets all the user profiles of users with at least one image, who haven't uploaded in over 2 months"""

    from astrobin.models import Image, UserProfile

    recipientPks = []
    profiles = UserProfile.objects \
        .annotate(num_images=Count("user__image")) \
        .filter(num_images__gt=0)

    two_months_ago = timezone.now() - datetime.timedelta(days=60)

    for profile in profiles:
        images = Image.objects_including_wip.filter(user=profile.user).order_by("-uploaded")
        if images.count() > 0:
            last_uploaded = images[0].uploaded
            if last_uploaded < two_months_ago \
                    and (profile.inactive_account_reminder_sent is None
                         or profile.inactive_account_reminder_sent < two_months_ago):
                # This user has at least 1 upload but all of them are older than 2 months
                recipientPks.append(profile.pk)

    return UserProfile.objects.filter(pk__in=recipientPks)
