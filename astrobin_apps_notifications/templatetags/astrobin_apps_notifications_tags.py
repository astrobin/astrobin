# Django
from django.template import Library

# This app
from astrobin_apps_notifications.utils import (
    get_seen_notifications,
    get_unseen_notifications,
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
