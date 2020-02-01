import datetime

from django.template import Library

from astrobin_apps_premium.utils import premium_get_valid_usersubscription

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
    if not user.is_authenticated():
        return False

    userSubscription = premium_get_valid_usersubscription(user)
    if userSubscription:
        return userSubscription.subscription.group.name == "astrobin_ultimate_2020"
    return False


@register.filter
def is_any_premium(user):
    return is_premium(user) | is_premium_2020(user)


@register.filter
def is_premium_2020(user):
    if not user.is_authenticated():
        return False

    userSubscription = premium_get_valid_usersubscription(user)
    if userSubscription:
        return userSubscription.subscription.group.name == "astrobin_premium_2020"
    return False


@register.filter
def is_premium(user):
    if not user.is_authenticated():
        return False

    userSubscription = premium_get_valid_usersubscription(user)
    if userSubscription:
        return userSubscription.subscription.group.name == "astrobin_premium"
    return False


@register.filter
def is_any_lite(user):
    return is_lite(user) | is_lite_2020(user)


@register.filter
def is_lite_2020(user):
    if not user.is_authenticated():
        return False

    userSubscription = premium_get_valid_usersubscription(user)
    if userSubscription:
        return userSubscription.subscription.group.name == "astrobin_lite_2020"
    return False


@register.filter
def is_lite(user):
    if not user.is_authenticated():
        return False

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
def has_ultimate(user):
    return is_ultimate_2020(user)


@register.filter
def is_offer(subscription):
    return "offer" in subscription.category


@register.filter
def can_view_full_technical_card(user):
    return not is_free(user)


@register.filter
def can_view_technical_card_item(user, item):
    if is_free(user):
        return False

    allowed_items = [
        "Imaging telescope or lens",
        "Imaging camera",
        "Resolution"
    ]

    return item[0] in allowed_items and item[1] is not None
