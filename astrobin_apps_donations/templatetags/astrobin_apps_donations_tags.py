# Python
import urllib

# Django
from django.conf import settings
from django.template import Library, Node

# Third party
from subscription.models import Subscription, UserSubscription


register = Library()


@register.inclusion_tag('astrobin_apps_donations/inclusion_tags/donate_modal.html', takes_context = True)
def donate_modal(context):
    return {
        'base_url': settings.ASTROBIN_BASE_URL,
        'business': settings.SUBSCRIPTION_PAYPAL_SETTINGS['business'],
        'subscription': Subscription.objects.get(name = 'AstroBin Donor'),
        'request': context['request'],
    }


@register.inclusion_tag('astrobin_apps_donations/inclusion_tags/remove_ads_modal.html', takes_context = True)
def remove_ads_modal(context):
    return {
        'base_url': settings.ASTROBIN_BASE_URL,
        'business': settings.SUBSCRIPTION_PAYPAL_SETTINGS['business'],
        'subscription': Subscription.objects.get(name = 'AstroBin Donor'),
        'request': context['request'],
    }


@register.inclusion_tag('astrobin_apps_donations/inclusion_tags/cancel_modal.html', takes_context = True)
def cancel_donation_modal(context):
    if settings.PAYPAL_TEST:
        cancel_url = 'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_subscr-find&alias=%s' % urllib.quote(settings.PAYPAL_RECEIVER_EMAIL)
    else:
        cancel_url = 'https://www.paypal.com/cgi-bin/webscr?cmd=_subscr-find&alias=%s' % urllib.quote(settings.PAYPAL_RECEIVER_EMAIL)

    return {
        'request': context['request'],
        'cancel_url': cancel_url,
    }


@register.inclusion_tag('astrobin_apps_donations/inclusion_tags/donor_badge.html')
def donor_badge(user, size = 'large'):
    return {
        'user': user,
        'size': size,
    }


@register.filter
def is_donor(user):
    if user.is_authenticated():
        return UserSubscription.objects.filter(user = user, subscription__name = 'AstroBin Donor').count() > 0
    return False


@register.inclusion_tag('astrobin_apps_donations/inclusion_tags/thank_you_for_your_support.html', takes_context = True)
def thank_you_for_your_support(context):
    return {}

