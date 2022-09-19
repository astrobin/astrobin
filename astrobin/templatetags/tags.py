# -*- coding: utf-8 -*-
import math
from datetime import date, datetime

import dateutil
from annoying.functions import get_object_or_None
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.search import TrigramDistance
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.template import Library
from django.template.defaultfilters import timesince
from django.utils.safestring import SafeString, mark_safe
from django.utils.translation import ugettext as _
from pybb.models import Post, Topic
from subscription.models import Subscription, UserSubscription
from threaded_messages.models import Participant, Thread

from astrobin import utils
from astrobin.enums import SubjectType
from astrobin.enums.license import License
from astrobin.gear import get_correct_gear, is_gear_complete
from astrobin.models import GearUserInfo, Image, LICENSE_CHOICES, UserProfile
from astrobin.services.gear_service import GearService
from astrobin.services.utils_service import UtilsService
from astrobin.utils import (
    dec_decimal_precision_from_pixel_scale, decimal_to_degrees_minutes_seconds_html,
    decimal_to_hours_minutes_seconds_html, get_client_country_code, get_image_resolution,
    ra_decimal_precision_from_pixel_scale,
)
from astrobin_apps_donations.templatetags.astrobin_apps_donations_tags import is_donor
from astrobin_apps_equipment.models import EquipmentBrandListing, EquipmentItemListing
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import (
    is_any_ultimate, is_free, is_lite,
    is_lite_2020, is_premium, is_premium_2020, is_ultimate_2020,
)
from astrobin_apps_remote_source_affiliation.services.remote_source_affiliation_service import \
    RemoteSourceAffiliationService
from astrobin_apps_users.services import UserService

register = Library()


@register.filter
def split(value, arg):
    return value.split(arg)


@register.filter
def startswith(x, y):
    if x is None or y is None:
        return False
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
    paginate_by = kwargs.get('paginate_by', settings.EL_PAGINATION_PER_PAGE)
    alias = kwargs.get('alias', 'gallery')
    nav_ctx = kwargs.get('nav_ctx', None)
    nav_ctx_extra = kwargs.get('nav_ctx_extra', None)
    fancybox = kwargs.get('fancybox', True)

    view = kwargs.get('view')
    if view is None and 'view' in context:
        view = context['view']
    if view is None:
        view = context['request'].GET.get('view', 'default')

    return {
        'image_list': object_list,
        'request': context['request'],
        'paginate_by': paginate_by,
        'alias': alias,
        'view': view,
        'nav_ctx': nav_ctx,
        'nav_ctx_extra': nav_ctx_extra,
        'fancybox': fancybox,
    }


register.inclusion_tag('inclusion_tags/image_list.html', takes_context=True)(image_list)


@register.inclusion_tag('inclusion_tags/search_image_list.html', takes_context=True)
def search_image_list(context, paginate=True, **kwargs):
    request = context['request']
    q = request.GET.get('q')
    telescope = request.GET.get('telescope')
    camera = request.GET.get('camera')
    country = get_client_country_code(request)
    equipment_brand_listings = None
    equipment_item_listings = None

    if telescope or camera or q:
        equipment_brand_listings = EquipmentBrandListing.objects \
            .annotate(distance=TrigramDistance('brand__name', telescope or camera or q)) \
            .filter(distance__lte=.85, retailer__countries__icontains=country)
        equipment_item_listings = EquipmentItemListing.objects \
            .annotate(distance=TrigramDistance('name', telescope or camera or q)) \
            .filter(distance__lte=.5, retailer__countries__icontains=country)

    context.update({
        'paginate': paginate,
        'search_domain': context['request'].GET.get('d'),
        'sort': context['request'].GET.get('sort'),
        'equipment_brand_listings': equipment_brand_listings,
        'equipment_item_listings': equipment_item_listings,
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


@register.filter
def gear_modded(gear, user):
    gear_user_info: GearUserInfo = get_object_or_None(GearUserInfo, gear=gear, user=user)
    if gear_user_info:
        return gear_user_info.modded

    return False


@register.simple_tag
def gear_name_iriencoded(gear):
    from django.template.defaultfilters import iriencode
    name = str(gear)
    return iriencode(name)


@register.simple_tag
def gear_owners(gear):
    gear, gear_type = get_correct_gear(gear.id)
    return UserProfile.objects.filter(
        **{UserProfile.GEAR_ATTR_LOOKUP[gear_type]: gear}).count()


@register.simple_tag
def gear_set_owners(gear_set):
    owners = 0
    for g in gear_set.all():
        owners += gear_owners(g)

    return owners


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
def show_ads(user: User, user_subscription: UserSubscription):
    if not settings.ADS_ENABLED:
        return False

    if is_donor(user) and not user.userprofile.allow_astronomy_ads:
        return False

    if is_lite(user_subscription) or is_premium(user_subscription):
        return False

    if (is_premium_2020(user_subscription) or is_ultimate_2020(user_subscription)) and not \
            user.userprofile.allow_astronomy_ads:
        return False

    return True


@register.simple_tag(takes_context=True)
def show_ads_on_page(context):
    request = context['request']

    valid_subscription = context.context_processors['astrobin.context_processors.user_profile']['valid_usersubscription']

    if not show_ads(request.user, valid_subscription):
        return False

    if context.template_name == 'image/detail.html':
        for data in context.dicts:
            if 'image' in data:
                image_owner_valid_user_subscription = PremiumService(data['image'].user).get_valid_usersubscription()
                return not is_any_ultimate(image_owner_valid_user_subscription)
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
                requested_user_valid_usersubscription = PremiumService(
                    data['requested_user']
                ).get_valid_usersubscription()
                return not is_any_ultimate(requested_user_valid_usersubscription)
    elif context.template_name == 'index/root.html':
        return show_ads(request.user, valid_subscription) and is_free(valid_subscription)
    elif context.template_name in (
            'search/search.html',
            'top_picks.html',
            'astrobin_apps_iotd/iotd_archive.html'
    ):
        return not request.user.is_authenticated or is_free(valid_subscription)

    return False


@register.simple_tag(takes_context=True)
def show_secondary_ad_on_page(context):
    request = context['request']

    valid_subscription = context.context_processors['astrobin.context_processors.user_profile']['valid_usersubscription']

    if not show_ads(request.user, valid_subscription):
        return False

    country = utils.get_client_country_code(request)
    if country.lower() not in ('us', 'ca'):
        return False

    if context.template_name == 'image/detail.html':
        for data in context.dicts:
            if 'image' in data:
                image_owner_valid_user_subscription = PremiumService(data['image'].user).get_valid_usersubscription()
                return (
                        (not request.user.is_authenticated or is_free(valid_subscription)) and
                        not is_any_ultimate(image_owner_valid_user_subscription)
                )
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
                requested_user_valid_usersubscription = PremiumService(
                    data['requested_user']
                ).get_valid_usersubscription()
                return (
                        (not request.user.is_authenticated or is_free(valid_subscription)) and
                        not is_any_ultimate(requested_user_valid_usersubscription)
                )

    return False


@register.simple_tag(takes_context=True)
def show_skyscraper_ads_on_page(context):
    request = context['request']

    valid_subscription = context.context_processors['astrobin.context_processors.user_profile']['valid_usersubscription']

    if not show_ads(request.user, valid_subscription):
        return False

    country = utils.get_client_country_code(request)
    if country.lower() not in ('us', 'ca'):
        return False

    is_anon = not context['request'].user.is_authenticated
    image_owner_is_ultimate = False

    if context.template_name.startswith('registration/'):
        return False
    elif context.template_name == 'image/detail.html':
        for data in context.dicts:
            if 'image' in data:
                image_owner_valid_user_subscription = PremiumService(data['image'].user).get_valid_usersubscription()
                image_owner_is_ultimate = is_any_ultimate(image_owner_valid_user_subscription)
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
                requested_user_valid_usersubscription = PremiumService(data['requested_user']).get_valid_usersubscription()
                image_owner_is_ultimate = is_any_ultimate(requested_user_valid_usersubscription)

    return (is_anon or is_free(valid_subscription)) and not image_owner_is_ultimate and \
           (context["COOKIELAW_ACCEPTED"] is not False or not show_cookie_banner(context.request))


@register.filter()
def image_ad_key_value_pairs(image):
    if RemoteSourceAffiliationService.is_remote_source_affiliate(image.remote_source):
        return {
            "exclude-category": "remote-hosting"
        }

    return None


@register.filter
def valid_subscriptions(user):
    if user.is_anonymous:
        return []

    us = UserSubscription.active_objects.filter(user=user)
    subs = [x.subscription for x in us if x.active and x.expires >= date.today()]
    return subs


@register.filter
def inactive_subscriptions(user):
    if user.is_anonymous:
        return []

    return [x.subscription
            for x
            in UserSubscription.objects.filter(user=user)
            if not x.active or x.expires < date.today()]


@register.filter
def has_valid_subscription(user, subscription_pk):
    if user.is_anonymous:
        return False

    us = UserSubscription.active_objects.filter(
        user=user, subscription__pk=subscription_pk)

    if us.count() == 0:
        return False

    return us[0].active and us[0].expires >= date.today()


@register.filter
def has_valid_subscription_in_category(user, category):
    if user.is_anonymous:
        return False

    us = UserSubscription.active_objects.filter(
        user=user, subscription__category__contains=category)

    if us.count() == 0:
        return False

    return us[0].active and us[0].expires >= date.today()


@register.filter
def get_paid_subscription_expiration(user_subscription: UserSubscription):
    if not user_subscription:
        return None

    if user_subscription and user_subscription.user.is_anonymous:
        return None

    return user_subscription.expires


@register.filter
def has_subscription_by_name(user, name):
    if user.is_anonymous:
        return False

    return UserSubscription.objects.filter(
        user=user, subscription__name=name).count() > 0


@register.filter
def get_usersubscription_by_name(user, name):
    if user.is_anonymous:
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
    return UserService(user).is_in_group('content_moderators')

@register.filter
def is_image_moderator(user):
    return UserService(user).is_in_group('image_moderators')

@register.filter
def is_forum_moderator(user):
    return UserService(user).is_in_group('forum_moderators')

@register.filter
def can_like(user, target):
    return UserService(user).can_like(target)


@register.filter
def can_like_reason(user, target):
    return UserService(user).can_like_reason(target)


@register.filter
def can_unlike(user, target):
    return UserService(user).can_unlike(target)


@register.filter
def can_unlike_reason(user, target):
    return UserService(user).can_unlike_reason(target)


@register.filter
def humanize_image_acquisition_type(type):
    for choice in Image.ACQUISITION_TYPE_CHOICES:
        if type == choice[0]:
            return choice[1]
    return ""


@register.filter
def ra_to_hms(degrees, pixel_scale=0):
    if pixel_scale is None:
        pixel_scale = 0

    precision = ra_decimal_precision_from_pixel_scale(pixel_scale)
    return mark_safe(decimal_to_hours_minutes_seconds_html(degrees, precision=precision))


@register.filter
def dec_to_dms(degrees, pixel_scale=0):
    if pixel_scale is None:
        pixel_scale = 0

    precision = dec_decimal_precision_from_pixel_scale(pixel_scale)
    return mark_safe(decimal_to_degrees_minutes_seconds_html(degrees, precision=precision))


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
        SubjectType.NOCTILUCENT_CLOUDS,
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
        'pt',
        'zh-hans',
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
        'uk',
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
        'uk': 'Українська',
        'ru': 'Русский',
        'sq': 'Shqipe',
        'tr': 'Türkçe',
        'zh-hans': '中文 (简体)',
    }

    try:
        return languages[language_code.lower()]
    except KeyError:
        return 'English (US)'


@register.simple_tag
def get_language_code_display(language_code):
    languages = {
        '': 'EN',
        'en': 'EN',
        'en-us': 'EN',
        'en-gb': 'EN (GB)',

        'ar': 'AR',
        'de': 'DE',
        'el': 'EL',
        'es': 'ES',
        'fi': 'FI',
        'fr': 'FR',
        'it': 'IT',
        'ja': 'JA',
        'nl': 'NL',
        'pl': 'PL',
        'pt': 'PT',
        'pt-br': 'PT (BR)',
        'ru': 'RU',
        'sq': 'SQ',
        'tr': 'TR',
        'uk': 'UK',
        'zh-hans': 'ZH (CN)',
    }

    try:
        return languages[language_code.lower()]
    except KeyError:
        return 'EN'


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

    if requesting_user.is_authenticated and requesting_user.userprofile.exclude_from_competitions:
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
def show_click_and_drag_zoom(request) -> bool:
    return (not 'real' in request.GET and
            not (request.user_agent.is_touch_capable or
                 request.user_agent.is_mobile or
                 request.user_agent.is_tablet))


@register.simple_tag
def show_10_year_anniversary_logo():
    # type: () -> bool
    return UtilsService.show_10_year_anniversary_logo()


@register.filter
def show_images_used(user_subscription: UserSubscription) -> bool:
    return is_lite_2020(user_subscription)


@register.filter
def show_uploads_used(user_subscription: UserSubscription):
    return is_free(user_subscription) or is_lite(user_subscription)


@register.filter
def show_cookie_banner(request):
    country = utils.get_client_country_code(request)
    return country is None or country.lower() in utils.get_european_union_country_codes()


@register.filter
def post_is_unread(post, request):
    first_unread_created_string = request.session.get('first_unread_for_topic_%d' % post.topic.pk)

    if first_unread_created_string:
        first_unread_created = dateutil.parser.parse(first_unread_created_string)
        return post.created >= first_unread_created and post.user != request.user

    return False


@register.filter
def first_unread_post_link(topic, request):
    if 'first_unread_for_topic_%d_post' % topic.pk in request.session:
        post = Post.objects.get(pk=request.session['first_unread_for_topic_%d_post' % topic.pk])
        if post == post.topic.last_post and post.user == request.user:
            return None
        return settings.BASE_URL + post.get_absolute_url()

    return None


@register.simple_tag
def license_logo(image):
    # type: (Image) -> SafeString

    icons = {
        License.ALL_RIGHTS_RESERVED: 'cc/c.png',
        License.ATTRIBUTION_NON_COMMERCIAL_SHARE_ALIKE: 'cc/cc-by-nc-sa.png',
        License.ATTRIBUTION_NON_COMMERCIAL: 'cc/cc-by-nc.png',
        License.ATTRIBUTION_NON_COMMERCIAL_NO_DERIVS: 'cc/cc-by-nc-nd.png',
        License.ATTRIBUTION: 'cc/cc-by.png',
        License.ATTRIBUTION_SHARE_ALIKE: 'cc/cc-by-sa.png',
        License.ATTRIBUTION_NO_DERIVS: 'cc/cc-by-nd.png',
    }

    license = image.license

    if type(image.license) == int:
        license = License.from_deprecated_integer(license)

    icon = static('astrobin/icons/%s' % icons[license])
    title = [x[1] for x in LICENSE_CHOICES if x[0] == license][0]

    return mark_safe('<img class="license" src="%s" alt="%s" title="%s" />' % (icon, title, title))


@register.simple_tag(takes_context=True)
def forum_latest_topics(context, cnt=5, user=None):
    if not user:
        user = context['user']

    if user and user.is_authenticated:
        qs = Topic.objects.filter(
            Q(forum__group=None) |
            Q(forum__group__owner=user) |
            Q(forum__group__members=user)
        )

        if not is_forum_moderator(user):
            qs = qs.filter(on_moderation=False)
    else:
        qs = Topic.objects.filter(forum__group=None, on_moderation=False)

    qs = qs.distinct().select_related()

    return qs.order_by('-updated', '-id')[:cnt]


@register.simple_tag(takes_context=True)
def use_high_contrast_theme(context):
    if 'request' not in context:
        return False

    request = context.get('request')
    cookie = request.COOKIES.get('astrobin_use_high_contrast_theme')
    return cookie is not None


@register.filter
def participation_is_deleted(thread: Thread, user: User) -> bool:
    participations = Participant.objects.filter(thread=thread, user=user)

    if not participations.exists():
        return True

    return participations[0].deleted_at != None


@register.filter
def has_unmigrated_legacy_gear_items(user: User) -> bool:
    return GearService.has_unmigrated_legacy_gear_items(user)
