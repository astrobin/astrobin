import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q, QuerySet
from django.template import Library
from subscription.models import UserSubscription

from astrobin.enums.full_size_display_limitation import FullSizeDisplayLimitation
from astrobin.models import Image
from astrobin_apps_premium.services.premium_service import PremiumService
from common.services import DateTimeService

register = Library()


@register.inclusion_tag('astrobin_apps_premium/inclusion_tags/premium_badge.html')
def premium_badge(user, size='large'):
    return {
        'user': user,
        'size': size,
    }


@register.filter
def get_valid_usersubscription(user: User) -> UserSubscription:
    return PremiumService(user).get_valid_usersubscription()


@register.filter
def is_any_ultimate(user_subscription: UserSubscription) -> bool:
    return is_ultimate_2020(user_subscription)


@register.filter
def is_ultimate_2020(user_subscription: UserSubscription) -> bool:
    if user_subscription:
        return user_subscription.subscription.group.name == "astrobin_ultimate_2020"
    return False


@register.filter
def is_any_premium(user_subscription: UserSubscription) -> bool:
    return is_premium(user_subscription) | is_premium_2020(user_subscription)


@register.filter
def is_premium_2020(user_subscription: UserSubscription) -> bool:
    if user_subscription:
        return user_subscription.subscription.group.name == "astrobin_premium_2020"
    return False


@register.filter
def is_premium(user_subscription: UserSubscription) -> bool:
    if user_subscription:
        return user_subscription.subscription.group.name == "astrobin_premium"
    return False


@register.filter
def is_any_lite(user_subscription: UserSubscription) -> bool:
    return is_lite(user_subscription) | is_lite_2020(user_subscription)


@register.filter
def is_lite_2020(user_subscription: UserSubscription) -> bool:
    if user_subscription:
        return user_subscription.subscription.group.name == "astrobin_lite_2020"
    return False


@register.filter
def is_lite(user_subscription: UserSubscription) -> bool:
    if user_subscription:
        return user_subscription.subscription.group.name == "astrobin_lite"
    return False


@register.filter
def is_free(user_subscription: UserSubscription) -> bool:
    return not is_any_paid_subscription(user_subscription)


@register.filter
def is_any_paid_subscription(user_subscription: UserSubscription) -> bool:
    return \
        is_lite(user_subscription) or \
        is_premium(user_subscription) or \
        is_lite_2020(user_subscription) or \
        is_premium_2020(user_subscription) or \
        is_ultimate_2020(user_subscription)


@register.filter
def has_expired_paid_subscription(user: User) -> bool:
    cache_key = "has_an_expired_premium_subscription_%d" % user.pk

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    valid_subscription = PremiumService(user).get_valid_usersubscription()
    if is_any_paid_subscription(valid_subscription):
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
def has_paid_subscription_near_expiration(user, days):
    cache_key = "has_premium_subscription_near_expiration_%d" % user.pk

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    if has_expired_paid_subscription(PremiumService(user).get_valid_usersubscription()):
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
def can_view_full_technical_card(user: User) -> bool:
    return True


@register.filter
def can_view_technical_card_item(user: User, item) -> bool:
    if not item[1]:
        return False

    if isinstance(item[1], QuerySet):
        return len(item[1]) > 0

    return True


@register.filter
def can_access_advanced_search(user_subscription: UserSubscription) -> bool:
    return not is_free(user_subscription)


@register.filter
def can_access_full_search(user_subscription: UserSubscription) -> bool:
    # Pre 2020 Lite and Premium for continuity reasons
    return is_lite(user_subscription) or is_premium(user_subscription) or is_any_ultimate(user_subscription)


@register.filter
def can_perform_basic_platesolving(user_subscription: UserSubscription) -> bool:
    return not is_free(user_subscription)


@register.filter
def can_perform_advanced_platesolving(user_subscription: UserSubscription) -> bool:
    return is_any_ultimate(user_subscription)


@register.filter
def can_see_real_resolution(user: User, image: Image) -> bool:
    if image.full_size_display_limitation == FullSizeDisplayLimitation.EVERYBODY:
        return True

    if image.full_size_display_limitation == FullSizeDisplayLimitation.PAYING_MEMBERS_ONLY:
        return not is_free(PremiumService(user).get_valid_usersubscription()) or user == image.user

    if image.full_size_display_limitation == FullSizeDisplayLimitation.MEMBERS_ONLY:
        return user.is_authenticated

    if image.full_size_display_limitation == FullSizeDisplayLimitation.ME_ONLY:
        return user == image.user

    return False


@register.filter
def can_restore_from_trash(user_subscription: UserSubscription) -> bool:
    return is_any_ultimate(user_subscription)


@register.filter
def can_remove_ads(user_subscription: UserSubscription) -> bool:
    if not settings.ADS_ENABLED:
        return False

    if is_lite(user_subscription) or is_any_premium(user_subscription) or is_any_ultimate(user_subscription):
        return True

    return False


@register.filter
def allow_full_retailer_integration(
        viewer_user_subscription: UserSubscription, owner_user_subscription: UserSubscription
) -> bool:
    if not settings.ADS_ENABLED:
        return False

    if is_ultimate_2020(viewer_user_subscription) or is_ultimate_2020(owner_user_subscription):
        return False

    if is_free(viewer_user_subscription) or is_lite_2020(viewer_user_subscription):
        return True

    if (
            is_lite(viewer_user_subscription) or
            is_premium(viewer_user_subscription) or
            is_premium_2020(viewer_user_subscription)
    ):
        return viewer_user_subscription and viewer_user_subscription.user.userprofile.allow_retailer_integration

    return True


@register.filter
def allow_lite_retailer_integration(
        viewer_user_subscription: UserSubscription, owner_user_subscription: UserSubscription
) -> bool:
    if not settings.ADS_ENABLED:
        return False

    if is_lite(viewer_user_subscription) or is_premium(viewer_user_subscription) or is_premium_2020(
            viewer_user_subscription
    ):
        return viewer_user_subscription.user.userprofile.allow_retailer_integration and is_ultimate_2020(
            owner_user_subscription
        )

    if is_lite_2020(viewer_user_subscription):
        if is_ultimate_2020(owner_user_subscription):
            return owner_user_subscription.user.userprofile.allow_retailer_integration
        return False

    if is_ultimate_2020(viewer_user_subscription):
        return viewer_user_subscription.user.userprofile.allow_retailer_integration

    if is_ultimate_2020(owner_user_subscription):
        return owner_user_subscription and owner_user_subscription.user.userprofile.allow_retailer_integration

    if (
            is_free(viewer_user_subscription) or not (
            viewer_user_subscription and viewer_user_subscription.user.is_authenticated)
    ):
        return False

    return True


@register.filter
def can_remove_retailer_integration(user_subscription: UserSubscription) -> bool:
    return is_lite(user_subscription) or is_premium(user_subscription) or is_any_ultimate(user_subscription)


@register.filter
def can_upload_uncompressed_source(user_subscription: UserSubscription) -> bool:
    return is_any_ultimate(user_subscription)


@register.filter
def can_download_data(user_subscription: UserSubscription) -> bool:
    # This refers to bulk data export.
    return is_any_premium(user_subscription) or is_any_ultimate(user_subscription)
