import urllib

from django.template import Library

from astrobin_apps_notifications.utils import (
    get_seen_notifications,
    get_unseen_notifications, build_notification_url, get_notification_url_params_for_email
)

register = Library()


@register.inclusion_tag('astrobin_apps_notifications/table.html')
def notifications_table(user, unseen_count, seen_count):
    unseen = get_unseen_notifications(user, unseen_count)
    seen = get_seen_notifications(user, seen_count)

    return {
        'unseen': unseen,
        'seen': seen,
        'username': user.username
    }


@register.filter
def has_unseen_notifications(user):
    if not user.is_authenticated():
        return False
    return get_unseen_notifications(user, -1).count() > 0


@register.filter
def show_notice_settings(label):
    # type: (str) -> bool

    return label not in (
        'test_notification',
        'welcome_to_astrobin',
        'congratulations_for_your_first_image',
        'new_subscription',
        'new_payment',
        'iotd_staff_inactive_removal_notice',
        'iotd_staff_inactive_warning',
        'image_you_promoted_is_tp',
        'image_you_promoted_is_iotd',
    )


@register.filter
def to_notification_url(url):
    return build_notification_url(url)


@register.simple_tag
def notification_url_params_for_email(from_user=None):
    params = get_notification_url_params_for_email(from_user)
    return urllib.urlencode(params)
