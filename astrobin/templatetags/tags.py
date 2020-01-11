# -*- coding: utf-8 -*-

from math import floor

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template import Library
from django.template.defaultfilters import timesince
from django.utils.translation import ugettext as _

from astrobin.gear import *

register = Library()


@register.filter
def split(value, arg):
    return value.split(arg)


@register.filter
def startswith(x, y):
    return x.startswith(y)


@register.simple_tag
def current(request, pattern):
    import re
    if re.search(pattern, request.path):
        return 'active'
    return ''


@register.simple_tag
def in_gallery(request):
    import re
    if re.search('/users/[\w.@+-]+/(?:collections.*)?$', request.path):
        return 'visible'
    return 'hidden'


@register.simple_tag
def in_collection(request):
    import re
    if re.search('/users/[\w.@+-]+/collections/(\d+)/$', request.path):
        return 'visible'
    return 'hidden'


@register.inclusion_tag('inclusion_tags/related_images.html')
def related_images(request, object_list, type):
    paginator = Paginator(object_list, 12)

    page = request.GET.get('p')
    try:
        images = paginator.page(page)
    except (TypeError, PageNotAnInteger):
        images = paginator.page(1)
    except EmptyPage:
        images = paginator.page(paginator.num_pages)

    return {
        'request': request,
        'images': images,
        'related_type': type,
    }


@register.filter
def ago(date_time):
    date_time = date_time.replace(tzinfo=None)
    diff = abs(date_time - datetime.today())
    if diff.days <= 0:
        span = timesince(date_time)
        span = span.split(",")[0]  # just the most significant digit
        if span == "0 " + _("minutes"):
            return _("seconds ago")
        return _("%s ago") % span
    return datetime.date(date_time)


@register.filter
def date_before(date1, date2):
    return date1 < date2


@register.filter
def string_to_date(date):
    try:
        return datetime.strptime(date, "%Y-%m-%d")
    except:
        return datetime.now()


def image_list(context, object_list, **kwargs):
    alias = kwargs.get('alias', 'gallery')
    nav_ctx = kwargs.get('nav_ctx', 'all')
    nav_ctx_extra = kwargs.get('nav_ctx_extra', None)

    view = kwargs.get('view')
    if view is None and 'view' in context:
        view = context['view']
    if view is None:
        view = context['request'].GET.get('view', 'default')

    return {
        'image_list': object_list,
        'request': context['request'],
        'alias': alias,
        'view': view,
        'nav_ctx': nav_ctx,
        'nav_ctx_extra': nav_ctx_extra,
    }


register.inclusion_tag('inclusion_tags/image_list.html', takes_context=True)(image_list)


@register.inclusion_tag('inclusion_tags/search_image_list.html', takes_context=True)
def search_image_list(context, paginate=True, **kwargs):
    context.update({
        'paginate': paginate,
        'search_domain': context['request'].GET.get('d'),
        'sort': context['request'].GET.get('sort'),
    })

    return context


@register.filter
def seconds_to_hours(value):
    try:
        value = int(value)
    except ValueError:
        return "0"

    return "%.1f" % (int(value) / 3600.0)


@register.filter
def cut_decimals(value, places):
    try:
        value = float(value)
    except ValueError:
        return value

    return '{0:.{1}f}'.format(value, places)


@register.filter
def is_checkbox(value):
    from django.forms.fields import CheckboxInput
    return isinstance(value, CheckboxInput)


@register.inclusion_tag('inclusion_tags/list_gear.html')
def list_gear(label, gear, klass, user):
    return {
        'label': label,
        'gear': gear,
        'klass': klass,
        'user': user,
    }


@register.simple_tag
def gear_complete_class(gear):
    return 'incomplete' if not is_gear_complete(gear.id) else ''


@register.simple_tag
def gear_alias(gear, user):
    default = _("no alias")

    try:
        gear_user_info = GearUserInfo.objects.get(gear=gear, user=user)
        if gear_user_info.alias:
            return gear_user_info.alias
    except GearUserInfo.DoesNotExist:
        pass

    return default


@register.simple_tag
def gear_name_iriencoded(gear):
    from django.template.defaultfilters import iriencode
    name = unicode(gear)
    return iriencode(name)


@register.simple_tag
def gear_owners(gear):
    gear, gear_type = get_correct_gear(gear.id)
    return UserProfile.objects.filter(
        **{UserProfile.GEAR_ATTR_LOOKUP[gear_type]: gear}).count()


@register.simple_tag
def gear_set_images(gear_set):
    images = 0
    for g in gear_set.all():
        images += gear_images(g)

    return images


@register.simple_tag
def gear_set_owners(gear_set):
    owners = 0
    for g in gear_set.all():
        owners += gear_owners(g)

    return owners


@register.simple_tag
def gear_images(gear):
    return Image.by_gear(gear).count()


@register.simple_tag
def gear_type(gear):
    from astrobin.gear import get_correct_gear, TYPES_LOOKUP
    real_gear, gear_type = get_correct_gear(gear.id)

    if real_gear and gear_type and hasattr(real_gear, 'type') and real_gear.type:
        try:
            t = [item for item in TYPES_LOOKUP[gear_type] if item[0] == real_gear.type][0][1]
            return t
        except KeyError:
            pass

    return '-'


@register.filter
def show_ads(user):
    from astrobin_apps_donations.templatetags.astrobin_apps_donations_tags import is_donor
    from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_premium, is_lite

    if not settings.ADS_ENABLED:
        return False

    if is_donor(user):
        return False

    if settings.PREMIUM_ENABLED and (is_lite(user) or is_premium(user)):
        return False

    return True


@register.filter
def valid_subscriptions(user):
    from subscription.models import UserSubscription

    if user.is_anonymous():
        return []

    us = UserSubscription.active_objects.filter(user=user)
    subs = [x.subscription for x in us if x.valid()]
    return subs


@register.filter
def inactive_subscriptions(user):
    from subscription.models import UserSubscription

    if user.is_anonymous():
        return []

    return [x.subscription
            for x
            in UserSubscription.objects.filter(user=user)
            if not x.valid() or not x.active]


@register.filter
def has_valid_subscription(user, subscription_pk):
    from subscription.models import UserSubscription

    if user.is_anonymous():
        return False

    us = UserSubscription.active_objects.filter(
        user=user, subscription__pk=subscription_pk)

    if us.count() == 0:
        return False

    return us[0].valid()


@register.filter
def has_valid_subscription_in_category(user, category):
    from subscription.models import UserSubscription

    if user.is_anonymous():
        return False

    us = UserSubscription.active_objects.filter(
        user=user, subscription__category__contains=category)

    if us.count() == 0:
        return False

    return us[0].valid()


@register.filter
def get_premium_subscription_expiration(user):
    from subscription.models import UserSubscription

    if user.is_anonymous():
        return None

    us = UserSubscription.active_objects.filter(
        user=user,
        subscription__group__name__in=['astrobin_premium', 'astrobin_lite'])

    if us.count() == 0:
        return None

    return us[0].expires


@register.filter
def has_subscription_by_name(user, name):
    from subscription.models import UserSubscription

    if user.is_anonymous():
        return False

    return UserSubscription.objects.filter(
        user=user, subscription__name=name).count() > 0


@register.filter
def get_subscription_by_name(user, name):
    from subscription.models import UserSubscription

    if user.is_anonymous():
        return None

    return UserSubscription.objects.get(
        user=user, subscription__name=name)


@register.filter
def is_content_moderator(user):
    if not user.is_authenticated():
        return False

    return user.groups.filter(name='content_moderators').count() > 0


@register.filter
def is_image_moderator(user):
    if not user.is_authenticated():
        return False

    return user.groups.filter(name='image_moderators').count() > 0


@register.filter
def to_user_timezone(value, user):
    from astrobin.utils import to_user_timezone as tut
    if user.is_authenticated():
        return tut(value, user.userprofile)
    return value


@register.filter
def can_like(user, image):
    from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free

    user_scores_index = 0
    min_index_to_like = settings.MIN_INDEX_TO_LIKE

    if user.is_authenticated():
        user_scores_index = user.userprofile.get_scores()['user_scores_index']

    if user.is_superuser:
        return True

    if user == image.user:
        return False

    if is_free(user) and user_scores_index < min_index_to_like:
        return False

    return True


@register.filter
def humanize_image_acquisition_type(type):
    for choice in Image.ACQUISITION_TYPE_CHOICES:
        if type == choice[0]:
            return choice[1]
    return ""


def decimal_to_hours_minutes_seconds(value, hour_symbol="h", minute_symbol="'", second_symbol="\""):
    is_positive = value >= 0
    value = abs(value)
    hours = int(value / 15)
    minutes = int(((value / 15) - hours) * 60)
    seconds = ((((value / 15) - hours) * 60) - minutes) * 60

    return "%s%d%s %d%s %d%s" % (
        "" if is_positive else "-",
        hours, hour_symbol,
        minutes, minute_symbol,
        seconds, second_symbol)


def decimal_to_degrees_minutes_seconds(value, degree_symbol="°", minute_symbol="'", second_symbol="\""):
    is_positive = value >= 0
    value = abs(value)
    minutes, seconds = divmod(value * 3600, 60)
    degrees, minutes = divmod(minutes, 60)

    return "%s%d%s %d%s %d%s" % (
        "+" if is_positive else "-",
        degrees, degree_symbol,
        minutes, minute_symbol,
        seconds, second_symbol)


@register.filter
def ra_to_hms(degrees):
    return decimal_to_hours_minutes_seconds(degrees)


@register.filter
def dec_to_dms(degrees):
    return decimal_to_degrees_minutes_seconds(degrees)
