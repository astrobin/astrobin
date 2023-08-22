from django.contrib.auth.models import User
from django.template import Library
from subscription.models import UserSubscription

from astrobin.models import Image
from astrobin_apps_premium.services.premium_service import PremiumService

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
    return PremiumService.is_any_ultimate(user_subscription)


@register.filter
def is_ultimate_2020(user_subscription: UserSubscription) -> bool:
    return PremiumService.is_ultimate_2020(user_subscription)


@register.filter
def is_any_premium(user_subscription: UserSubscription) -> bool:
    return PremiumService.is_any_premium(user_subscription)


@register.filter
def is_premium_2020(user_subscription: UserSubscription) -> bool:
    return PremiumService.is_premium_2020(user_subscription)


@register.filter
def is_premium(user_subscription: UserSubscription) -> bool:
    return PremiumService.is_premium(user_subscription)


@register.filter
def is_any_lite(user_subscription: UserSubscription) -> bool:
    return PremiumService.is_any_lite(user_subscription)


@register.filter
def is_lite_2020(user_subscription: UserSubscription) -> bool:
    return PremiumService.is_lite_2020(user_subscription)


@register.filter
def is_lite(user_subscription: UserSubscription) -> bool:
    return PremiumService.is_lite(user_subscription)


@register.filter
def is_free(user_subscription: UserSubscription) -> bool:
    return PremiumService.is_free(user_subscription)


@register.filter
def is_any_paid_subscription(user_subscription: UserSubscription) -> bool:
    return PremiumService.is_any_paid_subscription(user_subscription)


@register.filter
def has_expired_paid_subscription(user: User) -> bool:
    return PremiumService.has_expired_paid_subscription(user)


@register.filter
def has_paid_subscription_near_expiration(user, days):
    return PremiumService.has_paid_subscription_near_expiration(user)


@register.filter
def can_view_full_technical_card(user: User) -> bool:
    return PremiumService.can_view_full_technical_card(user)


@register.filter
def can_view_technical_card_item(user: User, item) -> bool:
    return PremiumService.can_view_technical_card_item(user, item)


@register.filter
def can_access_advanced_search(user_subscription: UserSubscription) -> bool:
    return PremiumService.can_access_advanced_search(user_subscription)


@register.filter
def can_access_full_search(user_subscription: UserSubscription) -> bool:
    return PremiumService.can_access_full_search(user_subscription)


@register.filter
def can_perform_basic_platesolving(user_subscription: UserSubscription) -> bool:
    return PremiumService.can_perform_basic_platesolving(user_subscription)


@register.filter
def can_perform_advanced_platesolving(user_subscription: UserSubscription) -> bool:
    return PremiumService.can_perform_advanced_platesolving(user_subscription)


@register.filter
def can_see_real_resolution(user: User, image: Image) -> bool:
    if image.video_file.name:
        return False

    return PremiumService.can_see_real_resolution(user, image)


@register.filter
def can_restore_from_trash(user_subscription: UserSubscription) -> bool:
    return PremiumService.can_restore_from_trash(user_subscription)


@register.filter
def can_remove_ads(user_subscription: UserSubscription) -> bool:
    return PremiumService.can_remove_ads(user_subscription)


@register.filter
def allow_full_retailer_integration(
        viewer_user_subscription: UserSubscription, owner_user_subscription: UserSubscription
) -> bool:
    return PremiumService.allow_full_retailer_integration(viewer_user_subscription, owner_user_subscription)


@register.filter
def can_remove_retailer_integration(user_subscription: UserSubscription) -> bool:
    return PremiumService.can_remove_retailer_integration(user_subscription)


@register.filter
def can_upload_uncompressed_source(user_subscription: UserSubscription) -> bool:
    return PremiumService.can_upload_uncompressed_source(user_subscription)


@register.filter
def can_download_data(user_subscription: UserSubscription) -> bool:
    return PremiumService.can_download_data(user_subscription)
