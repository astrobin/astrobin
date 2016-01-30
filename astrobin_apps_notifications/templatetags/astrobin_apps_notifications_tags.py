# Django
from django.template import Library

# This app
from astrobin_apps_notifications.utils import (
    get_seen_notifications,
    get_unseen_notifications,
)


register = Library()


@register.inclusion_tag('astrobin_apps_notifications/list.html')
def notification_list(user, unseen_count, seen_count):
    unseen = get_unseen_notifications(user, unseen_count)
    seen = get_seen_notifications(user, seen_count)

    return {
        'unseen' : unseen,
        'seen'   : seen,
    }
