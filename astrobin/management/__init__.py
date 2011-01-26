from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _
from notification import models as notification

def create_notice_types(app, created_models, verbosity, **kwargs):
    notification.create_notice_type(
        'new_follower',
        _('A user is following you'),
        _('Your new images will be notified to them'))

    notification.create_notice_type(
        'follow_success',
        _('You are now folling'),
        _('Their new images will be notified to you'))

    notification.create_notice_type(
        'unfollow_success',
        _('You are not following anymore'),
        _('Their new images will not be notified to you anymore'))

    notification.create_notice_type(
        'new_image',
        _('New image'),
        _('A user you follow has published a new image'))


signals.post_syncdb.connect(create_notice_types, sender=notification)

