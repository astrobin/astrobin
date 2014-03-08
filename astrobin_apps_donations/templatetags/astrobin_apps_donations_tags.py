# Python
import urllib

# Django
from django.conf import settings
from django.db.models import Q
from django.template import Library, Node

# Third party
from subscription.models import Subscription, UserSubscription


register = Library()


@register.inclusion_tag('astrobin_apps_donations/inclusion_tags/donate_modal.html', takes_context = True)
def donate_modal(context):
    return {
        'base_url': settings.ASTROBIN_BASE_URL,
        'business': settings.SUBSCRIPTION_PAYPAL_SETTINGS['business'],

        'monthly_coffee_sub': Subscription.objects.get(name = 'AstroBin Donor Coffee Monthly'),
        'monthly_snack_sub': Subscription.objects.get(name = 'AstroBin Donor Snack Monthly'),
        'monthly_pizza_sub': Subscription.objects.get(name = 'AstroBin Donor Pizza Monthly'),
        'monthly_movie_sub': Subscription.objects.get(name = 'AstroBin Donor Movie Monthly'),
        'monthly_dinner_sub': Subscription.objects.get(name = 'AstroBin Donor Dinner Monthly'),

        'yearly_coffee_sub': Subscription.objects.get(name = 'AstroBin Donor Coffee Yearly'),
        'yearly_snack_sub': Subscription.objects.get(name = 'AstroBin Donor Snack Yearly'),
        'yearly_pizza_sub': Subscription.objects.get(name = 'AstroBin Donor Pizza Yearly'),
        'yearly_movie_sub': Subscription.objects.get(name = 'AstroBin Donor Movie Yearly'),
        'yearly_dinner_sub': Subscription.objects.get(name = 'AstroBin Donor Dinner Yearly'),

        'request': context['request'],
    }


@register.inclusion_tag('astrobin_apps_donations/inclusion_tags/remove_ads_modal.html', takes_context = True)
def remove_ads_modal(context):
    return {
        'base_url': settings.ASTROBIN_BASE_URL,
        'business': settings.SUBSCRIPTION_PAYPAL_SETTINGS['business'],

        'monthly_coffee_sub': Subscription.objects.get(name = 'AstroBin Donor Coffee Monthly'),
        'monthly_snack_sub': Subscription.objects.get(name = 'AstroBin Donor Snack Monthly'),
        'monthly_pizza_sub': Subscription.objects.get(name = 'AstroBin Donor Pizza Monthly'),
        'monthly_movie_sub': Subscription.objects.get(name = 'AstroBin Donor Movie Monthly'),
        'monthly_dinner_sub': Subscription.objects.get(name = 'AstroBin Donor Dinner Monthly'),

        'yearly_coffee_sub': Subscription.objects.get(name = 'AstroBin Donor Coffee Yearly'),
        'yearly_snack_sub': Subscription.objects.get(name = 'AstroBin Donor Snack Yearly'),
        'yearly_pizza_sub': Subscription.objects.get(name = 'AstroBin Donor Pizza Yearly'),
        'yearly_movie_sub': Subscription.objects.get(name = 'AstroBin Donor Movie Yearly'),
        'yearly_dinner_sub': Subscription.objects.get(name = 'AstroBin Donor Dinner Yearly'),

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
        try:
            us = UserSubscription.objects.get(
                Q(user = user) &
                Q(
                    Q(subscription__name = 'AstroBin Donor Coffee Monthly') |
                    Q(subscription__name = 'AstroBin Donor Snack Monthly') |
                    Q(subscription__name = 'AstroBin Donor Pizza Monthly') |
                    Q(subscription__name = 'AstroBin Donor Movie Monthly') |
                    Q(subscription__name = 'AstroBin Donor Dinner Monthly') |

                    Q(subscription__name = 'AstroBin Donor Coffee Yearly') |
                    Q(subscription__name = 'AstroBin Donor Snack Yearly') |
                    Q(subscription__name = 'AstroBin Donor Pizza Yearly') |
                    Q(subscription__name = 'AstroBin Donor Movie Yearly') |
                    Q(subscription__name = 'AstroBin Donor Dinner Yearly')
                ))
        except UserSubscription.DoesNotExist:
            return False

        return us.valid()

    return False


@register.filter
def has_donation_subscription(user, name):
    if user.is_authenticated():
        try:
            us = UserSubscription.objects.get(
                Q(user = user) & Q(subscription__name = name))
        except UserSubscription.DoesNotExist:
            return False

        return us.valid()

    return False


@register.simple_tag(takes_context = True)
def donation_form_selected(context, name):
    request = context['request']
    selected = 'selected="selected"'

    if has_donation_subscription(request.user, name):
        return selected

    if not is_donor(request.user) and name == 'AstroBin Donor Pizza Monthly':
        return selected

    return ''


@register.inclusion_tag('astrobin_apps_donations/inclusion_tags/thank_you_for_your_support.html', takes_context = True)
def thank_you_for_your_support(context):
    return {}

