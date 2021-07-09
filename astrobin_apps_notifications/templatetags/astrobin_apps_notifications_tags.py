import urllib.request, urllib.parse, urllib.error

from django.template import Library

from astrobin_apps_notifications.utils import get_notification_url_params_for_email

register = Library()


@register.simple_tag
def notification_url_params_for_email(from_user=None):
    params = get_notification_url_params_for_email(from_user)
    return urllib.parse.urlencode(params)
