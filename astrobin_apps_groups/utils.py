from django.contrib.auth.models import User

from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_lite, is_premium, is_premium_2020, \
    is_lite_2020, is_ultimate_2020


def has_access_to_premium_group_features(user):
    # type: (User) -> bool
    return is_lite(user) \
           or is_premium(user) \
           or is_lite_2020(user) \
           or is_premium_2020(user) \
           or is_ultimate_2020(user)
