from subscription.models import UserSubscription

from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import (
    is_lite, is_lite_2020, is_premium,
    is_premium_2020, is_ultimate_2020,
)


def has_access_to_premium_group_features(user_subscription: UserSubscription) -> bool:
    return is_lite(user_subscription) \
           or is_premium(user_subscription) \
           or is_lite_2020(user_subscription) \
           or is_premium_2020(user_subscription) \
           or is_ultimate_2020(user_subscription)
