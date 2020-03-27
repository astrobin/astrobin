# Python

# Django
from django.conf import settings
from django.db.models import Q
from django.template import Library

# Third party
from subscription.models import UserSubscription

register = Library()


@register.inclusion_tag('astrobin_apps_donations/inclusion_tags/cancel_modal.html', takes_context=True)
def cancel_donation_modal(context):
    if settings.PAYPAL_TEST:
        cancel_url = 'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_subscr-find&alias=%s' % settings.PAYPAL_MERCHANT_ID
    else:
        cancel_url = 'https://www.paypal.com/cgi-bin/webscr?cmd=_subscr-find&alias=%s' % settings.PAYPAL_MERCHANT_ID

    return {
        'request': context['request'],
        'cancel_url': cancel_url,
    }


@register.inclusion_tag('astrobin_apps_donations/inclusion_tags/donor_badge.html')
def donor_badge(user, size='large'):
    return {
        'user': user,
        'size': size,
    }


@register.filter
def is_donor(user):
    if settings.DONATIONS_ENABLED and user.is_authenticated():
        us = UserSubscription.objects.filter(
            Q(user=user) &
            Q(
                Q(subscription__name='AstroBin Donor Coffee Monthly') |
                Q(subscription__name='AstroBin Donor Snack Monthly') |
                Q(subscription__name='AstroBin Donor Pizza Monthly') |
                Q(subscription__name='AstroBin Donor Movie Monthly') |
                Q(subscription__name='AstroBin Donor Dinner Monthly') |

                Q(subscription__name='AstroBin Donor Coffee Yearly') |
                Q(subscription__name='AstroBin Donor Snack Yearly') |
                Q(subscription__name='AstroBin Donor Pizza Yearly') |
                Q(subscription__name='AstroBin Donor Movie Yearly') |
                Q(subscription__name='AstroBin Donor Dinner Yearly') |

                Q(subscription__name='AstroBin Donor Bronze Monthly') |
                Q(subscription__name='AstroBin Donor Silver Monthly') |
                Q(subscription__name='AstroBin Donor Gold Monthly') |
                Q(subscription__name='AstroBin Donor Platinum Monthly') |

                Q(subscription__name='AstroBin Donor Bronze Yearly') |
                Q(subscription__name='AstroBin Donor Silver Yearly') |
                Q(subscription__name='AstroBin Donor Gold Yearly') |
                Q(subscription__name='AstroBin Donor Platinum Yearly')
            ))

        if us.count() == 0:
            return False

        us = us[0]
        return us.valid()

    return False


@register.filter
def has_donation_subscription(user, name):
    if settings.DONATIONS_ENABLED and user.is_authenticated():
        us = UserSubscription.objects.filter(
            Q(user=user) & Q(subscription__name=name))

        if us.count() == 0:
            return False

        us = us[0]
        return us.valid()

    return False


@register.simple_tag(takes_context=True)
def donation_form_selected(context, name):
    request = context['request']
    selected = 'selected="selected"'

    if has_donation_subscription(request.user, name):
        return selected

    if not is_donor(request.user) and name == 'AstroBin Donor Gold Monthly':
        return selected

    return ''


@register.simple_tag
def user_donation_subscription(user):
    if settings.DONATIONS_ENABLED and user.is_authenticated():
        try:
            us = UserSubscription.objects.get(
                Q(user=user) &
                Q(
                    Q(subscription__name='AstroBin Donor Coffee Monthly') |
                    Q(subscription__name='AstroBin Donor Snack Monthly') |
                    Q(subscription__name='AstroBin Donor Pizza Monthly') |
                    Q(subscription__name='AstroBin Donor Movie Monthly') |
                    Q(subscription__name='AstroBin Donor Dinner Monthly') |

                    Q(subscription__name='AstroBin Donor Coffee Yearly') |
                    Q(subscription__name='AstroBin Donor Snack Yearly') |
                    Q(subscription__name='AstroBin Donor Pizza Yearly') |
                    Q(subscription__name='AstroBin Donor Movie Yearly') |
                    Q(subscription__name='AstroBin Donor Dinner Yearly') |

                    Q(subscription__name='AstroBin Donor Bronze Monthly') |
                    Q(subscription__name='AstroBin Donor Silver Monthly') |
                    Q(subscription__name='AstroBin Donor Gold Monthly') |
                    Q(subscription__name='AstroBin Donor Platinum Monthly') |

                    Q(subscription__name='AstroBin Donor Bronze Yearly') |
                    Q(subscription__name='AstroBin Donor Silver Yearly') |
                    Q(subscription__name='AstroBin Donor Gold Yearly') |
                    Q(subscription__name='AstroBin Donor Platinum Yearly')
                ))
        except UserSubscription.DoesNotExist:
            return None

        return us.subscription

    return None


@register.simple_tag
def user_donation_subscription_name(user):
    if settings.DONATIONS_ENABLED:
        us = user_donation_subscription(user)
        if us:
            return us.name
    return ''


@register.simple_tag
def user_donation_subscription_id(user):
    if settings.DONATIONS_ENABLED:
        us = user_donation_subscription(user)
        if us:
            return us.id
    return 0


@register.inclusion_tag('astrobin_apps_donations/inclusion_tags/thank_you_for_your_donations.html', takes_context=True)
def thank_you_for_your_donations(context):
    return {}
