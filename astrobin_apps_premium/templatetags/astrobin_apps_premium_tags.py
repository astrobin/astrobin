import datetime

from django.conf import settings
from django.db.models import QuerySet
from django.template import Library
from subscription.models import Subscription

from astrobin_apps_premium.utils import premium_get_valid_usersubscription

register = Library()


@register.inclusion_tag('astrobin_apps_premium/inclusion_tags/premium_badge.html')
def premium_badge(user, size='large'):
    return {
        'user': user,
        'size': size,
    }


@register.filter
def show_renew_message(usersubscription):
    # type: (UserSubscription) -> bool
    return usersubscription is not None and usersubscription.valid() and usersubscription.subscription.name in [
        "AstroBin Lite",
        "AstroBin Lite 2020+",
        "AstroBin Premium",
        "AstroBin Premium 2020+",
        "AstroBin Ultimate 2020+"
    ]

@register.simple_tag
def offered_subscriptions():
    # type: () -> QuerySet
    return Subscription.objects.filter(name__in=[
        "AstroBin Lite 2020+",
        "AstroBin Premium 2020+",
        "AstroBin Ultimate 2020+",

        "AstroBin Raw Data Meteor 2020+",
        "AstroBin Raw Data Luna 2020+",
        "AstroBin Raw Data Sol 2020+",

        "AstroBin Donor Bronze Monthly",
        "AstroBin Donor Silver Monthly",
        "AstroBin Gold Silver Monthly",
        "AstroBin Platinum Silver Monthly",

        "AstroBin Donor Bronze Yearly",
        "AstroBin Donor Silver Yearly",
        "AstroBin Gold Silver Yearly",
        "AstroBin Platinum Silver Yearly",
    ])

@register.filter
def is_subscription_offered(subscription):
    # type: (Subscription) -> bool
    return subscription in offered_subscriptions()

@register.filter
def is_any_ultimate(user):
    return is_ultimate_2020(user)


@register.filter
def is_ultimate_2020(user):
    userSubscription = premium_get_valid_usersubscription(user)
    if userSubscription:
        return userSubscription.subscription.group.name == "astrobin_ultimate_2020"
    return False


@register.filter
def is_any_premium(user):
    return is_premium(user) | is_premium_2020(user)


@register.filter
def is_premium_2020(user):
    userSubscription = premium_get_valid_usersubscription(user)
    if userSubscription:
        return userSubscription.subscription.group.name == "astrobin_premium_2020"
    return False


@register.filter
def is_premium(user):
    userSubscription = premium_get_valid_usersubscription(user)
    if userSubscription:
        return userSubscription.subscription.group.name == "astrobin_premium"
    return False


@register.filter
def is_any_lite(user):
    return is_lite(user) | is_lite_2020(user)


@register.filter
def is_lite_2020(user):
    userSubscription = premium_get_valid_usersubscription(user)
    if userSubscription:
        return userSubscription.subscription.group.name == "astrobin_lite_2020"
    return False


@register.filter
def is_lite(user):
    userSubscription = premium_get_valid_usersubscription(user)
    if userSubscription:
        return userSubscription.subscription.group.name == "astrobin_lite"
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
def can_upload_uncompressed_source(user):
    return is_any_ultimate(user)


@register.filter
def can_download_data(user):
    # This refers to bulk data export.
    return is_any_premium(user) or is_any_ultimate(user)
