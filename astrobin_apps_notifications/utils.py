from urllib.parse import parse_qsl, urlparse, urlencode, urlunparse

from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.utils.safestring import mark_safe

from notification import models as notification


def clear_notifications_template_cache(username):
    key = make_template_fragment_key('notifications_table', [username])
    cache.delete(key)


def push_notification(recipients, from_user, notice_type, data):
    data.update({
        'notices_url': settings.BASE_URL + '/',
        'base_url': settings.BASE_URL,
    })
    notification.send(recipients, notice_type, data, sender=from_user)
    for recipient in recipients:
        clear_notifications_template_cache(recipient.username)


def get_notification_url_params_for_email(from_user=None, additional_query_args=None):
    result = dict(
        utm_source='astrobin',
        utm_medium='email',
        utm_campaign='notification',
        from_user=from_user.pk if from_user else None
    )

    if additional_query_args:
        result = {**result, **additional_query_args}

    return result


def build_notification_url(url, from_user=None, additional_query_args=None):
    params = get_notification_url_params_for_email(from_user, additional_query_args)
    url_parse = urlparse(url)
    query = url_parse.query
    url_dict = dict(parse_qsl(query))
    url_dict.update(params)
    url_new_query = urlencode(url_dict)
    url_parse = url_parse._replace(query=url_new_query)
    return mark_safe(urlunparse(url_parse))
