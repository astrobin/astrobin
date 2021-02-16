import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import QuerySet, Q
from django.template import Library
from subscription.models import Subscription, UserSubscription

from astrobin_apps_premium.utils import premium_get_valid_usersubscription
from common.services import DateTimeService

register = Library()


@register.inclusion_tag('astrobin_apps_premium/inclusion_tags/premium_badge.html')
def premium_badge(user, size='large'):
    return {
        'user': user,
        'size': size,
    }


@register.filter
def is_any_ultimate(user):
    return is_ultimate_2020(user)


@register.filter
def is_ultimate_2020(user):
    user_subscription = premium_get_valid_usersubscription(user)
    if user_subscription:
        return user_subscription.subscription.group.name == "astrobin_ultimate_2020"
    return False


@register.filter
def is_any_premium(user):
    return is_premium(user) | is_premium_2020(user)


@register.filter
def is_premium_2020(user):
    user_subscription = premium_get_valid_usersubscription(user)
    if user_subscription:
        return user_subscription.subscription.group.name == "astrobin_premium_2020"
    return False


@register.filter
def is_premium(user):
    user_subscription = premium_get_valid_usersubscription(user)
    if user_subscription:
        return user_subscription.subscription.group.name == "astrobin_premium"
    return False


@register.filter
def is_any_lite(user):
    return is_lite(user) | is_lite_2020(user)


@register.filter
def is_lite_2020(user):
    user_subscription = premium_get_valid_usersubscription(user)
    if user_subscription:
        return user_subscription.subscription.group.name == "astrobin_lite_2020"
    return False


@register.filter
def is_lite(user):
    user_subscription = premium_get_valid_usersubscription(user)
    if user_subscription:
        return user_subscription.subscription.group.name == "astrobin_lite"
    return False


@register.filter
def is_free(user):
    return not is_any_premium_subscription(user)


@register.filter
def is_any_premium_subscription(user):
    return \
        is_lite(user) or \
        is_premium(user) or \
        is_lite_2020(user) or \
        is_premium_2020(user) or \
        is_ultimate_2020(user)


@register.filter
def has_an_expired_premium_subscription(user):
    cache_key = "has_an_expired_premium_subscription_%d" % user.pk

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    if is_any_premium_subscription(user):
        result = False
    else:
        result = UserSubscription.objects.filter(
            user=user,
            expires__lt=DateTimeService.today(),
            subscription__category__contains="premium"
        ).exists()

    cache.set(cache_key, result, 300)
    return result


@register.filter
def has_premium_subscription_near_expiration(user, days):
    cache_key = "has_premium_subscription_near_expiration_%d" % user.pk

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    if has_an_expired_premium_subscription(user):
        result = False
    else:
        result = UserSubscription.objects.filter(
            Q(user=user) &
            Q(active=True) &
            Q(expires__lt=DateTimeService.today() + datetime.timedelta(days)) &
            Q(expires__gt=DateTimeService.today()) &
            Q(subscription__category__contains="premium")
        ).exists()

    cache.set(cache_key, result, 300)
    return result


@register.filter
def is_usersubscription_current(user_subscription):
    # type: (UserSubscription) -> bool
    return user_subscription and user_subscription.active and user_subscription.expires >= datetime.date.today()


@register.filter
def has_valid_premium_offer(user):
    return user.userprofile.premium_offer \
           and user.userprofile.premium_offer_expiration \
           and user.userprofile.premium_offer_expiration > datetime.datetime.now()


@register.filter
def is_offer(subscription):
    return "offer" in subscription.category


@register.filter
def can_view_full_technical_card(user):
    return True


@register.filter
def can_view_technical_card_item(user, item):
    if not item[1]:
        return False

    if isinstance(item[1], QuerySet):
        return len(item[1]) > 0

    return True


@register.filter
def can_access_advanced_search(user):
    return not is_free(user)


@register.filter
def can_access_full_search(user):
    # Pre 2020 Lite and Premium for continuity reasons
    return is_lite(user) or is_premium(user) or is_any_ultimate(user)


@register.filter
def can_perform_basic_platesolving(user):
    return not is_free(user)


@register.filter
def can_perform_advanced_platesolving(user):
    return is_any_ultimate(user)


@register.filter
def can_see_real_resolution(user, image):
    return not is_free(user) or \
           user == image.user or \
           is_any_ultimate(image.user) or \
           is_premium(image.user) or \
           is_lite(image.user)


@register.filter
def can_restore_from_trash(user):
    return is_any_ultimate(user)


@register.filter
def can_remove_ads(user):
    if not settings.ADS_ENABLED:
        return False

    if is_lite(user) or is_any_premium(user) or is_any_ultimate(user):
        return True

    return False


@register.filter
def allow_full_retailer_integration(viewer, owner):
    # type: (User, User) -> bool

    if not settings.ADS_ENABLED:
        return False

    if is_ultimate_2020(viewer) or is_ultimate_2020(owner):
        return False

    if is_free(viewer) or is_lite_2020(viewer):
        return True

    if is_lite(viewer) or is_premium(viewer) or is_premium_2020(viewer):
        return viewer.userprofile.allow_retailer_integration

    return True


@register.filter
def allow_lite_retailer_integration(viewer, owner):
    # type: (User, User) -> bool

    if not settings.ADS_ENABLED:
        return False

    if is_lite(viewer) or is_premium(viewer) or is_premium_2020(viewer):
        return viewer.userprofile.allow_retailer_integration and is_ultimate_2020(owner)

    if is_lite_2020(viewer):
        if is_ultimate_2020(owner):
            return owner.userprofile.allow_retailer_integration
        return False

    if is_ultimate_2020(viewer):
        return viewer.userprofile.allow_retailer_integration

    if is_ultimate_2020(owner):
        return owner.userprofile.allow_retailer_integration

    if is_free(viewer) or not viewer.is_authenticated:
        return False

    return True


@register.filter
def can_remove_retailer_integration(user):
    return is_lite(user) or is_premium(user) or is_any_ultimate(user)


@register.filter
def can_upload_uncompressed_source(user):
    return is_any_ultimate(user)


@register.filter
def can_download_data(user):
    # This refers to bulk data export.
    return is_any_premium(user) or is_any_ultimate(user)
