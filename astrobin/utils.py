# -*- coding: utf-8 -*-
import datetime
import logging
from typing import List, Tuple

from django.contrib.auth.models import User
from django.contrib.gis.geoip2 import GeoIP2
from django.core.files.images import get_image_dimensions
from django.db.models import Count
from django.utils import timezone

logger = logging.getLogger(__name__)


def unique_items(list_with_possible_duplicates):
    """
    Given an initial list, returns a list but without duplicates
    """
    try:
        return list(set(list_with_possible_duplicates))
    except TypeError:
        # We have a list which is not flat, use the old way to remove duplicates
        found = []
        for i in list_with_possible_duplicates:
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


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_client_country_code(request) -> str:
    default_country = 'UNKNOWN'

    try:
        debug_country = request.GET.get('DEBUG_COUNTRY', None)
        if debug_country:
            return debug_country
    except AttributeError:
        pass

    geoip2 = GeoIP2()

    try:
        country = geoip2.country_code(get_client_ip(request))
        if country is None:
            country = default_country
        return country
    except Exception as e:
        logger.error("Error getting country code: %s" % e)
        return default_country


def get_gdpr_country_codes() -> List[str]:
    return [
        'AT',  # Austria
        'BE',  # Belgium
        'BG',  # Bulgaria
        'CY',  # Cyprus
        'CZ',  # Czech Republic
        'DE',  # Germany
        'DK',  # Denmark
        'EE',  # Estonia
        'ES',  # Spain
        'FI',  # Finland
        'FR',  # France
        'GB',  # United Kingdom
        'GR',  # Greece
        'HR',  # Croatia
        'HU',  # Hungary
        'IE',  # Ireland
        'IT',  # Italy
        'LT',  # Lithuania
        'LU',  # Luxembourg
        'LV',  # Latvia
        'MT',  # Malta
        'NL',  # The Netherlands
        'PL',  # Poland
        'PT',  # Portugal
        'RO',  # Romania
        'SE',  # Sweden
        'SI',  # Slovenia
        'SK',  # Slovakia
    ]


def inactive_accounts():
    """Gets all the user profiles of users with at least one image, who haven't uploaded in over 2 months"""

    from astrobin.models import Image, UserProfile

    recipient_pks = []
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
                recipient_pks.append(profile.pk)

    return UserProfile.objects.filter(pk__in=recipient_pks)


def never_activated_accounts():
    """Gets all the users who created account over 2 weeks ago but never activated it."""

    two_weeks_ago = timezone.now() - datetime.timedelta(days=14)
    return User.objects.filter(
        is_active=False,
        date_joined__lt=two_weeks_ago,
        userprofile__never_activated_account_reminder_sent__isnull=True,
        userprofile__deleted__isnull=True,
    )


def never_activated_accounts_to_be_deleted():
    """Gets all the users who created account over 3 weeks ago but never activated it."""

    three_weeks_ago = timezone.now() - datetime.timedelta(days=21)
    return User.objects.filter(
        is_active=False,
        date_joined__lt=three_weeks_ago,
        userprofile__never_activated_account_reminder_sent__isnull=False,
        userprofile__deleted__isnull=True,
    )


def uniq(seq):
    # Not order preserving
    keys = {}
    for e in seq:
        keys[e] = 1
    return list(keys.keys())


def uniq_id_tuple(seq):
    seen = set()
    ret = []
    for e in seq:
        id = e[0]
        if id not in seen:
            seen.add(id)
            ret.append(e)
    return ret


def get_image_resolution(image):
    try:
        w, h = image.w, image.h
        if not (w and h):
            w, h = get_image_dimensions(image.image_file)
    except (FileNotFoundError, TypeError) as e:
        # This might happen in unit tests
        logger.warning("utils.get_image_resolution: unable to get image dimensions for %d: %s" % (image.pk, str(e)))
        w, h = 0, 0

    return w, h


def dec_decimal_precision_from_pixel_scale(pixel_scale: float = 0) -> int:
    if pixel_scale == 0 or pixel_scale > 10:
        return 0

    if pixel_scale > 1:
        return 1

    return 2

def ra_decimal_precision_from_pixel_scale(pixel_scale: float = 0) -> int:
    return dec_decimal_precision_from_pixel_scale(pixel_scale) + 1


def number_unit_decimals(value, unit, precision, must_be_less_than=None):
    if must_be_less_than is not None and int(round(value)) >= must_be_less_than:
        value = must_be_less_than - pow(10, -precision)

    if precision == 0:
        value = f'{int(round(value))}{unit}'
    else:
        decimal_part = ("%s" % round((value - int(value)) * pow(10, precision))).ljust(precision, '0')
        value = f'{int(value)}{unit}.{decimal_part}'

    return value


def number_unit_decimals_html(value, unit, precision, must_be_less_than=None):
    if must_be_less_than is not None and int(round(value)) >= must_be_less_than:
        value = must_be_less_than - pow(10, -precision)

    if precision == 0:
        value = '%s<span class="symbol">%s</span>' % (("%d" % value).rjust(2, '0'), unit)
    else:
        decimal_part = ("%s" % round((value - int(value)) * pow(10, precision))).ljust(precision, '0')
        value = '%s<span class="symbol">%s</span>.%s' % (("%d" % value).rjust(2, '0'), unit, decimal_part)

    return value

def decimal_to_hours_minutes_seconds(value):
    value = abs(value)
    hours = int(value / 15)
    minutes = int(((value / 15) - hours) * 60)
    seconds = ((((value / 15) - hours) * 60) - minutes) * 60

    return hours, minutes, seconds

def decimal_to_hours_minutes_seconds_string(value, hour_symbol="h", minute_symbol="m", second_symbol="s", precision=0):
    hours, minutes, seconds = decimal_to_hours_minutes_seconds(value)
    is_positive = value >= 0
    seconds = number_unit_decimals(seconds, second_symbol, precision, must_be_less_than=60)

    return f'{"" if is_positive else "-"}{hours}{hour_symbol} {minutes}{minute_symbol} {seconds}'


def decimal_to_hours_minutes_seconds_html(value, hour_symbol="h", minute_symbol="m", second_symbol="s", precision=0):
    hours, minutes, seconds = decimal_to_hours_minutes_seconds(value)
    is_positive = value >= 0
    seconds = number_unit_decimals_html(seconds, second_symbol, precision, must_be_less_than=60)

    hours = '%s%s<span class="symbol">%s</span>' % ("" if is_positive else "-", ("%d"% hours).rjust(2, '0'), hour_symbol)
    minutes = '%s<span class="symbol">%s</span>' % (("%d" % minutes).rjust(2, '0'), minute_symbol)

    return f'{hours}{minutes}{seconds}'


def decimal_to_degrees_minutes_seconds(value):
    value = abs(value)
    minutes, seconds = divmod(value * 3600, 60)
    degrees, minutes = divmod(minutes, 60)

    return degrees, minutes, seconds

def decimal_to_degrees_minutes_seconds_string(value, degree_symbol="°", minute_symbol="&prime;", second_symbol="&Prime;", precision=0):
    is_positive = value >= 0
    degrees, minutes, seconds = decimal_to_degrees_minutes_seconds(value)
    seconds = number_unit_decimals(seconds, second_symbol, precision, must_be_less_than=60)

    return f'{"+" if is_positive else "-"}{int(degrees)}{degree_symbol} {int(minutes)}{minute_symbol} {seconds}'


def decimal_to_degrees_minutes_seconds_html(value, degree_symbol="°", minute_symbol="′", second_symbol="″", precision=0):
    is_positive = value >= 0
    degrees, minutes, seconds = decimal_to_degrees_minutes_seconds(value)
    seconds = number_unit_decimals_html(seconds, second_symbol, precision, must_be_less_than=60)

    degrees = '%s%s<span class="symbol">%s</span>' % ("+" if is_positive else "-", ("%d" % degrees).rjust(2, '0'), degree_symbol)
    minutes = '%s<span class="symbol">%s</span>' % (("%d" % minutes).rjust(2, '0'), minute_symbol)

    return f'{degrees}{minutes}{seconds}'


def degrees_minutes_seconds_to_decimal_degrees(degrees, minutes, seconds, direction):
    if seconds is None:
        seconds = 0

    if minutes is None:
        minutes = 0

    if degrees is None:
        degrees = 0

    dd = float(degrees) + float(minutes) / 60 + float(seconds) / (60 * 60)

    if direction == 'E' or direction == 'N':
        dd *= -1

    return dd
