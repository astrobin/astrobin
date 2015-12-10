# Python
import urllib

# Django
from django.conf import settings
from django.db.models import Q
from django.template import Library, Node

# Third party
from subscription.models import Subscription, UserSubscription


register = Library()


@register.inclusion_tag('astrobin_apps_premium/inclusion_tags/premium_modal.html', takes_context = True)
def premium_modal(context):
    return {
        'base_url': settings.ASTROBIN_BASE_URL,
        'business': settings.SUBSCRIPTION_PAYPAL_SETTINGS['business'],

        'lite_sub': Subscription.objects.get(name = 'AstroBin Lite'),
        'premium_sub': Subscription.objects.get(name = 'AstroBin Premium'),

        'request': context['request'],
    }


@register.inclusion_tag('astrobin_apps_premium/inclusion_tags/remove_ads_modal.html', takes_context = True)
def remove_ads_modal(context):
    return {
        'base_url': settings.ASTROBIN_BASE_URL,
        'business': settings.SUBSCRIPTION_PAYPAL_SETTINGS['business'],

        'lite_sub': Subscription.objects.get(name = 'AstroBin Lite'),
        'premium_sub': Subscription.objects.get(name = 'AstroBin Premium'),

        'request': context['request'],
    }


@register.inclusion_tag('astrobin_apps_premium/inclusion_tags/cancel_modal.html', takes_context = True)
def cancel_premium_modal(context):
    if settings.PAYPAL_TEST:
        cancel_url = 'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_subscr-find&alias=%s' % urllib.quote(settings.PAYPAL_RECEIVER_EMAIL)
    else:
        cancel_url = 'https://www.paypal.com/cgi-bin/webscr?cmd=_subscr-find&alias=%s' % urllib.quote(settings.PAYPAL_RECEIVER_EMAIL)

    return {
        'request': context['request'],
        'cancel_url': cancel_url,
    }


@register.inclusion_tag('astrobin_apps_premium/inclusion_tags/premium.html')
def premium_badge(user, size = 'large'):
    return {
        'user': user,
        'size': size,
    }


@register.filter
def is_premium(user):
    if user.is_authenticated():
        us = UserSubscription.active_objects.filter(
            user = user,
            subscription__name = 'AstroBin Premium',
            cancelled = False
        )

        if us.count() == 0:
            return False

        us = us[0]
        return us.valid() and not us.expired()

    return False

@register.filter
def is_lite(user):
    if user.is_authenticated():
        us = UserSubscription.active_objects.filter(
            user = user,
            subscription__name = 'AstroBin Lite',
            cancelled = False
        )

        if us.count() == 0:
            return False

        us = us[0]
        return us.valid() and not us.expired()

    return False

@register.filter
def is_free(user):
    return not (is_lite(user) or is_premium(user))

@register.filter
def has_subscription(user, name):
    if user.is_authenticated():
        us = UserSubscription.objects.filter(
            Q(user = user) & Q(subscription__name = name))

        if us.count() == 0:
            return False

        us = us[0]
        return us.valid()

    return False


@register.simple_tag(takes_context = True)
def premium_form_selected(context, name):
    request = context['request']
    selected = 'selected="selected"'

    if has_subscription(request.user, name):
        return selected

    if not is_premium(request.user) and not is_lite(request.user) and name == 'AstroBin Premium Yearly':
        return selected

    return ''


@register.simple_tag
def user_premium_subscription(user):
    if user.is_authenticated():
        try:
            us = UserSubscription.objects.get(
                Q(user = user) &
                Q(
                    Q(subscription__name = 'AstroBin Premium') |
                    Q(subscription__name = 'AstroBin Lite')
                ))
        except UserSubscription.DoesNotExist:
            return None

        return us.subscription

    return None


@register.simple_tag
def user_premium_subscription_name(user):
    us = user_premium_subscription(user)
    if us:
        return us.name
    return ''


@register.simple_tag
def user_premium_subscription_id(user):
    us = user_premium_subscription(user)
    if us:
        return us.id
    return 0


@register.inclusion_tag('astrobin_apps_premium/inclusion_tags/thank_you_for_your_support.html', takes_context = True)
def thank_you_for_your_support(context):
    return {}
