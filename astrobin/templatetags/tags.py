# -*- coding: utf-8 -*-
import math
from datetime import datetime

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template import Library
from django.template.defaultfilters import timesince
from django.utils.translation import ugettext as _
from subscription.models import UserSubscription, Subscription

from astrobin.enums import SubjectType
from astrobin.gear import is_gear_complete, get_correct_gear
from astrobin.models import GearUserInfo, UserProfile, Image
from astrobin.utils import get_image_resolution, decimal_to_hours_minutes_seconds, decimal_to_degrees_minutes_seconds
from astrobin_apps_donations.templatetags.astrobin_apps_donations_tags import is_donor
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_premium_2020, is_premium, is_ultimate_2020, \
    is_lite
from astrobin_apps_premium.utils import premium_get_valid_usersubscription

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
    if not settings.ADS_ENABLED:
        return False

    if is_donor(user) and not user.userprofile.allow_astronomy_ads:
        return False

    if is_lite(user) or is_premium(user):
        return False

    if (is_premium_2020(user) or is_ultimate_2020(user)) and not user.userprofile.allow_astronomy_ads:
        return False

    return True


@register.filter
def valid_subscriptions(user):
    if user.is_anonymous():
        return []

    us = UserSubscription.active_objects.filter(user=user)
    subs = [x.subscription for x in us if x.valid()]
    return subs


@register.filter
def inactive_subscriptions(user):
    if user.is_anonymous():
        return []

    return [x.subscription
            for x
            in UserSubscription.objects.filter(user=user)
            if not x.valid() or not x.active]


@register.filter
def has_valid_subscription(user, subscription_pk):
    if user.is_anonymous():
        return False

    us = UserSubscription.active_objects.filter(
        user=user, subscription__pk=subscription_pk)

    if us.count() == 0:
        return False

    return us[0].valid()


@register.filter
def has_valid_subscription_in_category(user, category):
    if user.is_anonymous():
        return False

    us = UserSubscription.active_objects.filter(
        user=user, subscription__category__contains=category)

    if us.count() == 0:
        return False

    return us[0].valid()


@register.filter
def get_premium_subscription_expiration(user):
    if user.is_anonymous():
        return None

    us = premium_get_valid_usersubscription(user)
    return us.expires if us else None


@register.filter
def has_subscription_by_name(user, name):
    if user.is_anonymous():
        return False

    return UserSubscription.objects.filter(
        user=user, subscription__name=name).count() > 0


@register.filter
def get_usersubscription_by_name(user, name):
    if user.is_anonymous():
        return None

    return UserSubscription.objects.get(
        user=user, subscription__name=name)


@register.simple_tag
def get_subscription_by_name(name):
    return Subscription.objects.filter(name=name).first()


@register.simple_tag
def get_subscription_url_by_name(name):
    try:
        sub = Subscription.objects.get(name=name)
    except Subscription.DoesNotExist:
        return '#'

    return sub.get_absolute_url()


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
def is_forum_moderator(user):
    if not user.is_authenticated():
        return False

    return user.groups.filter(name='forum_moderators').count() > 0

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


@register.filter
def ra_to_hms(degrees):
    return decimal_to_hours_minutes_seconds(degrees)


@register.filter
def dec_to_dms(degrees):
    return decimal_to_degrees_minutes_seconds(degrees)


@register.filter
def thumbnail_width(image, alias):
    return min(settings.THUMBNAIL_ALIASES[''][alias]['size'][0], image.w)


@register.filter
def thumbnail_height(image, alias):
    thumb_w = min(settings.THUMBNAIL_ALIASES[''][alias]['size'][0], image.w)
    w, h = get_image_resolution(image)
    ratio = w / float(thumb_w)

    return math.floor(h / ratio)


@register.simple_tag
def thumbnail_scale(w, from_alias, to_alias):
    return min(settings.THUMBNAIL_ALIASES[''][to_alias]['size'][0], w) / \
           float(min(settings.THUMBNAIL_ALIASES[''][from_alias]['size'][0], w))


@register.filter
def gear_list_has_items(gear_list):
    for gear in gear_list:
        if len(gear[1]) > 0:
            return True

    return False


@register.filter
def content_type(obj):
    if not obj:
        return None
    return ContentType.objects.get_for_model(obj)


@register.inclusion_tag('inclusion_tags/private_abbr.html')
def private_abbr():
    return None


@register.filter
def can_add_technical_details(image):
    # type: (Image) -> bool
    return image.subject_type in (
        "", # Default as it comes from the frontend form.
        SubjectType.DEEP_SKY,
        SubjectType.SOLAR_SYSTEM,
        SubjectType.WIDE_FIELD,
        SubjectType.STAR_TRAILS,
        SubjectType.NORTHERN_LIGHTS,
    ) or image.solar_system_main_subject is not None


@register.simple_tag
def get_language_flag_icon(language_code, size=16):
    flags = {
        '': 'United-States.png',
        'en': 'United-States.png',
        'en-us': 'United-States.png',
        'en-gb': 'United-Kingdom.png',

        'ar': 'Saudi-Arabia.png',
        'de': 'Germany.png',
        'el': 'Greece.png',
        'es': 'Spain.png',
        'fi': 'Finland.png',
        'fr': 'France.png',
        'it': 'Italy.png',
        'ja': 'Japan.png',
        'nl': 'Netherlands.png',
        'pl': 'Poland.png',
        'pt-br': 'Brazil.png',
        'ru': 'Russia.png',
        'sq': 'Albania.png',
        'tr': 'Turkey.png',
    }

    return static('astrobin/icons/flags/%s/%s' % (size, flags[language_code.lower()]))
