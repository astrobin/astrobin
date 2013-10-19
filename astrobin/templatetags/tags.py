from datetime import datetime
import random
import string

from django.template.defaultfilters import timesince
from django.utils.translation import ugettext as _
from django.template import Library
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

from notification import models as notifications
from persistent_messages import models as messages
from celery.result import AsyncResult

from astrobin.models import Request
from astrobin.gear import *

register = Library()

@register.simple_tag
def current(request, pattern):
    import re
    if re.search(pattern, request.path):
        return 'active'
    return ''

@register.simple_tag
def in_gallery(request):
    import re
    if re.search('/users/[\w.@+-]+/$', request.path):
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


@register.inclusion_tag('inclusion_tags/notification_list.html')
def notification_list(request, show_footer = True, limit = 0):
    unseen = notifications.Notice.objects.filter(recipient = request.user, unseen = True)
    seen = notifications.Notice.objects.filter(recipient = request.user, unseen = False)

@register.inclusion_tag('inclusion_tags/request_list.html')
def request_list(request, show_footer = True):
    return {
        'requests':Request.objects.filter(to_user=request.user).order_by('-created').select_subclasses()[:10],
        'show_footer':show_footer}


@register.filter
def append_slash(value):
    return value.replace('\n', '\\\n')


@register.filter
def ago(date_time):
    date_time = date_time.replace(tzinfo = None)
    diff = abs(date_time - datetime.datetime.today())
    if diff.days <= 0:
        span = timesince(date_time)
        span = span.split(",")[0] # just the most significant digit
        if span == "0 " + _("minutes"):
            return _("seconds ago")
        return _("%s ago") % span
    return datetime.datetime.date(date_time)


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
    adjacent_pages = 3

    try:
        paginator = context['paginator']
        page = int(context['page'])
        pages = int(context['pages'])
        page_obj = context['page_obj']
        next = context['next']
        previous = context['previous']
        has_next = context['has_next']
        has_previous = context['has_previous']
    except:
        paginator = context['paginator']
        page_obj = context['page']
        page = page_obj.number
        pages = paginator.num_pages
        next = page_obj.next_page_number
        previous = page_obj.previous_page_number
        has_next = page_obj.has_next
        has_previous = page_obj.has_previous

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

    startPage = max(page - adjacent_pages, 1)
    if startPage <= 3: startPage = 1
    endPage = page + adjacent_pages + 1
    if endPage >= pages - 1: endPage = pages + 1
    page_numbers = [n for n in range(startPage, endPage) \
                    if n > 0 and n <= pages]

    request = context['request']
    return {
        'request': request,
        'STATIC_URL': settings.STATIC_URL,

        'page_obj': page_obj,
        'paginator': paginator,
        'page': page,
        'pages': pages,
        'page_numbers': page_numbers,
        'next': next,
        'previous': previous,
        'has_next': has_next,
        'has_previous': has_previous,
        'paginate': paginate,
        'show_first': 1 not in page_numbers,
        'show_last': pages not in page_numbers,

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


@register.simple_tag(takes_context = True)
def random_id(context, size = 8, chars = string.ascii_uppercase + string.digits):
    id = ''.join(random.choice(chars) for x in range(size))
    context['randomid'] = id
    return ''


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
def gear_name(gear):
    return "%s %s" % (gear.get_make(), gear.get_name())


@register.simple_tag
def gear_name_iriencoded(gear):
    from django.template.defaultfilters import iriencode
    name = gear_name(gear)
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

