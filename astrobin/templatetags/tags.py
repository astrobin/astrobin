# -*- coding: utf-8 -*-
import math
from datetime import datetime, date

from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template import Library
from django.template.defaultfilters import timesince
from django.utils.translation import ugettext as _
from subscription.models import UserSubscription, Subscription
from threaded_messages.models import Participant

from astrobin.enums import SubjectType
from astrobin.gear import is_gear_complete, get_correct_gear
from astrobin.models import GearUserInfo, UserProfile, Image
from astrobin.services.utils_service import UtilsService
from astrobin.utils import get_image_resolution, decimal_to_hours_minutes_seconds, decimal_to_degrees_minutes_seconds
from astrobin_apps_donations.templatetags.astrobin_apps_donations_tags import is_donor
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_premium_2020, is_premium, is_ultimate_2020, \
    is_lite, is_any_ultimate, is_free, is_lite_2020
from astrobin_apps_premium.utils import premium_get_valid_usersubscription
from astrobin_apps_users.services import UserService

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
            return '%s (%s)' % (gear_type, t)
        except KeyError:
            pass

    return gear_type


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


@register.simple_tag(takes_context=True)
def show_ads_on_page(context):
    request = context['request']

    if not show_ads(request.user):
        return False

    if context.template_name == 'image/detail.html':
        for data in context.dicts:
            if 'image' in data:
                return show_ads(request.user) and not is_any_ultimate(data['image'].user)
    elif context.template_name in (
            'user/profile.html',
            'user_collections_list.html',
            'user_collections_detail.html',
            'user/bookmarks.html',
            'user/liked.html',
            'user/following.html',
            'user/followers.html',
            'user/plots.html',
    ):
        for data in context.dicts:
            if 'requested_user' in data:
                return show_ads(request.user) and not is_any_ultimate(data['requested_user'])
    elif context.template_name == 'index/root.html':
        return show_ads(request.user) and is_free(request.user)
    elif context.template_name in (
            'search/search.html',
            'top_picks.html',
            'astrobin_apps_iotd/iotd_archive.html'
    ):
        return show_ads(request.user) and (not request.user.is_authenticated() or is_free(request.user))

    return False


@register.simple_tag(takes_context=True)
def show_adsense_ads(context):
    if not settings.ADSENSE_ENABLED:
        return False

    is_anon = not context['request'].user.is_authenticated()
    image_owner_is_ultimate = False

    if context.template_name.startswith('registration/'):
        return False
    elif context.template_name == 'image/detail.html':
        for data in context.dicts:
            if 'image' in data:
                image_owner_is_ultimate = is_any_ultimate(data['image'].user)
    elif context.template_name in (
            'user/profile.html',
            'user_collections_list.html',
            'user_collections_detail.html',
            'user/bookmarks.html',
            'user/liked.html',
            'user/following.html',
            'user/followers.html',
            'user/plots.html',
    ):
        for data in context.dicts:
            if 'requested_user' in data:
                image_owner_is_ultimate = is_any_ultimate(data['requested_user'])

    return is_anon and not image_owner_is_ultimate and \
           context["COOKIELAW_ACCEPTED"] is not False and \
           not context['request'].get_host().startswith("localhost")


@register.filter
def valid_subscriptions(user):
    if user.is_anonymous():
        return []

    us = UserSubscription.active_objects.filter(user=user)
    subs = [x.subscription for x in us if x.active and x.expires >= date.today()]
    return subs


@register.filter
def inactive_subscriptions(user):
    if user.is_anonymous():
        return []

    return [x.subscription
            for x
            in UserSubscription.objects.filter(user=user)
            if not x.active or x.expires < date.today()]


@register.filter
def has_valid_subscription(user, subscription_pk):
    if user.is_anonymous():
        return False

    us = UserSubscription.active_objects.filter(
        user=user, subscription__pk=subscription_pk)

    if us.count() == 0:
        return False

    return us[0].active and us[0].expires >= date.today()


@register.filter
def has_valid_subscription_in_category(user, category):
    if user.is_anonymous():
        return False

    us = UserSubscription.active_objects.filter(
        user=user, subscription__category__contains=category)

    if us.count() == 0:
        return False

    return us[0].active and us[0].expires >= date.today()


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
def can_like(user, target):
    return UserService(user).can_like(target)


@register.filter
def can_unlike(user, target):
    return UserService(user).can_unlike(target)


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


@register.inclusion_tag('inclusion_tags/private_abbr.html')
def private_abbr():
    return None


@register.filter
def can_add_technical_details(image):
    # type: (Image) -> bool
    return image.subject_type in (
        "",  # Default as it comes from the frontend form.
        SubjectType.DEEP_SKY,
        SubjectType.SOLAR_SYSTEM,
        SubjectType.WIDE_FIELD,
        SubjectType.STAR_TRAILS,
        SubjectType.NORTHERN_LIGHTS,
    ) or image.solar_system_main_subject is not None


@register.simple_tag
def get_native_languages():
    return ('en', 'en-GB')


@register.simple_tag
def get_officially_supported_languages():
    return (
        'de',
        'es',
        'fr',
        'it',
        'pt'
    )


@register.simple_tag
def get_other_languages():
    return (
        'ar',
        'el',
        'fi',
        'ja',
        'nl',
        'pl',
        'ru',
        'sq',
        'tr',
    )


@register.simple_tag
def get_language_name(language_code):
    languages = {
        '': 'English (US)',
        'en': 'English (US)',
        'en-us': 'English (US)',
        'en-gb': 'English (GB)',

        'ar': 'العربية',
        'de': 'Deutsch',
        'el': 'Ελληνικά',
        'es': 'Español',
        'fi': 'Suomi',
        'fr': 'Français',
        'it': 'Italiano',
        'ja': '日本語',
        'nl': 'Nederlands',
        'pl': 'Polski',
        'pt': 'Português',
        'pt-br': 'Português',
        'ru': 'Русский',
        'sq': 'Shqipe',
        'tr': 'Türk',
    }

    try:
        return languages[language_code.lower()]
    except KeyError:
        return 'English (US)'


@register.filter
def shadow_bans(a, b):
    # type: (User, User) -> bool
    return UserService(a).shadow_bans(b)


@register.filter
def skip_thread_list_shadow_bans(thread_list, user):
    # type: (QuerySet, User) -> QuerySet
    return Participant.objects.filter(pk__in=[
        x.pk for x in thread_list if not UserService(user).shadow_bans(x.thread.creator)
    ])


@register.filter
def in_upload_wizard(image, request):
    return not image.title or \
           "upload" in request.GET or \
           "upload" in request.POST


@register.simple_tag
def show_competitive_feature(requesting_user, target_user):
    if target_user and target_user.userprofile.exclude_from_competitions:
        return False

    if requesting_user.is_authenticated() and requesting_user.userprofile.exclude_from_competitions:
        return False

    return True


@register.simple_tag
def get_actstream_action_template_fragment_cache_key(action, language_code):
    cache_key = action.verb.replace('VERB_', '')

    if action.actor:
        cache_key += ".actor-%d" % action.actor.pk

    if action.action_object:
        cache_key += ".action-object-%d" % action.action_object.pk

    if action.target:
        cache_key += ".target-%d" % action.target.pk

    return "%s.%s" % (cache_key, language_code)


@register.filter
def show_click_and_drag_zoom(request, image):
    return (not 'real' in request.GET and
            not is_free(request.user) and
            not (request.user_agent.is_touch_capable or
                 request.user_agent.is_mobile or
                 request.user_agent.is_tablet))


@register.simple_tag
def show_10_year_anniversary_logo():
    # type: () -> bool
    return UtilsService.show_10_year_anniversary_logo()


@register.filter
def show_images_used(user):
    return is_lite_2020(user)


@register.filter
def show_uploads_used(user):
    return is_free(user) or is_lite(user)
