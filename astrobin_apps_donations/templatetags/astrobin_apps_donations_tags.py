# Django
from django.conf import settings
from django.template import Library, Node

# Third party
from subscription.models import Subscription

register = Library()

@register.inclusion_tag('astrobin_apps_donations/inclusion_tags/donate_modal.html', takes_context = True)
def donate_modal(context):
    return {
        'base_url': settings.ASTROBIN_BASE_URL,
        'business': settings.SUBSCRIPTION_PAYPAL_SETTINGS['business'],
        'subscription': Subscription.objects.get(name = 'AstroBin Donor'),
        'request': context['request'],
    }
