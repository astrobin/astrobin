from datetime import datetime
import random
import string

from django.template.defaultfilters import timesince
from django.utils.translation import ugettext as _
from django.template import Library
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from persistent_messages.models import Message
from celery.result import AsyncResult

from astrobin.models import Request
from astrobin.gear import *


register = Library()


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
    date_time = date_time.replace(tzinfo = None)
    diff = abs(date_time - datetime.today())
    if diff.days <= 0:
        span = timesince(date_time)
        span = span.split(",")[0] # just the most significant digit
        if span == "0 " + _("minutes"):
            return _("seconds ago")
        return _("%s ago") % span
    return datetime.date(date_time)


@register.filter
def string_to_date(date):
    try:
        return datetime.strptime(date, "%Y-%m-%d")
    except:
        return datetime.now()


def image_list(context, object_list, alias = 'gallery'):
    return {
        'image_list': object_list,
        'request': context['request'],
        'alias': alias,
        'view': context['request'].GET.get('view', 'default'),
        'STATIC_URL': settings.STATIC_URL,
    }
register.inclusion_tag('inclusion_tags/image_list.html', takes_context=True)(image_list)


@register.inclusion_tag('inclusion_tags/search_image_list.html', takes_context = True)
def search_image_list(context, object_list, paginate = True):
    user_list  = [x for x in object_list if x != None and x.verbose_name == 'User']
    gear_list  = [x for x in object_list if x != None and x.verbose_name == 'Gear']
    image_list = [x for x in object_list if x != None and x.verbose_name == 'Image']

    multiple = 0
    if len(user_list) > 0:
        multiple += 1
    if len(gear_list) > 0:
        multiple += 1
    if len(image_list) > 0:
        multiple += 1

    multiple = multiple > 1

    request = context['request']
    page = request.GET.get('page')
    if page is None:
        page = 1
    paginator = context['paginator']
    page_obj = paginator.page(page)

    return {
        'request': request,
        'STATIC_URL': settings.STATIC_URL,
        'paginate': paginate,
        'page_obj': page_obj,
        'show_first': True,
        'show_last': True,

        'user_list': user_list,
        'gear_list': gear_list,
        'image_list': image_list,

        'sort': request.GET.get('sort'),
        'search_type': request.GET.get('search_type', 0),
        'multiple': multiple,
        'view': request.GET.get('view', 'default'),
    }


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


@register.simple_tag
def search_form_query():
    query = '&amp;search_type=0'

    for i in range(0, 7):
        query += '&amp;license=%d' % i

    query += '&amp;telescope_type=any'
    for i in range(0, 23):
        query += '&amp;telescope_type=%d' % i

    query += '&amp;camera_type=any'
    for i in range(0, 6):
        query += '&amp;camera_type=%d' % i

    return query


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
        gear_user_info = GearUserInfo.objects.get(gear = gear, user = user)
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
            t = TYPES_LOOKUP[gear_type][real_gear.type][1]
            return t
        except KeyError:
            pass

    return '-'


@register.filter
def show_ads(user):
    from astrobin_apps_donations.templatetags.astrobin_apps_donations_tags import is_donor
    from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_premium, is_lite

    return (
        (settings.ADS_ENABLED and not is_donor(user)) and
        (settings.PREMIUM_ENABLED and not is_premium(user) and not is_lite(user))
    )


@register.filter
def valid_subscriptions(user):
    from subscription.models import UserSubscription

    if user.is_anonymous():
        return []

    us = UserSubscription.active_objects.filter(user = user)
    subs = [x.subscription for x in us if x.valid()]
    return subs


@register.filter
def has_valid_subscription(user, subscription_pk):
    from subscription.models import UserSubscription

    if user.is_anonymous():
        return False

    us = UserSubscription.active_objects.filter(
        user = user, subscription__pk = subscription_pk)

    if us.count() == 0:
        return False

    return us[0].valid()


@register.filter
def has_valid_subscription_in_category(user, category):
    from subscription.models import UserSubscription

    if user.is_anonymous():
        return False

    us = UserSubscription.active_objects.filter(
        user = user, subscription__category = category)

    if us.count() == 0:
        return False

    return us[0].valid()


@register.filter
def get_premium_subscription_expiration(user):
    from subscription.models import UserSubscription

    if user.is_anonymous():
        return None

    us = UserSubscription.active_objects.filter(
        user = user, subscription__category = 'premium')

    if us.count() == 0:
        return None

    return us[0].expires


@register.filter
def has_subscription_by_name(user, name):
    from subscription.models import UserSubscription

    if user.is_anonymous():
        return False

    return UserSubscription.objects.filter(
        user = user, subscription__name = name).count() > 0


@register.filter
def get_subscription_by_name(user, name):
    from subscription.models import UserSubscription

    if user.is_anonymous():
        return None

    return UserSubscription.objects.get(
        user = user, subscription__name = name)

@register.filter
def is_content_moderator(user):
    if not user.is_authenticated():
        return False

    return user.groups.filter(name='Content moderators').count() > 0


@register.filter
def to_user_timezone(value, user):
    from astrobin.utils import to_user_timezone as tut
    if user.is_authenticated():
        return tut(value, user.userprofile)
    return value
