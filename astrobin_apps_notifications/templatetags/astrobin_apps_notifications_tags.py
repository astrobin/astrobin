# Django
from django.template import Library

# This app
from astrobin_apps_notifications.utils import (
    get_seen_notifications,
    get_unseen_notifications,
)


register = Library()


@register.inclusion_tag('astrobin_apps_notifications/list.html')
def notification_list(user):
    unseen = get_unseen_notifications(user)
    seen = get_seen_notifications(user)

    return {
        'unseen' : unseen,
        'seen'   : seen,
    }
