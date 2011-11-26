from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _
from notification import models as notification

# Fields:
# 0 - notice label
# 1 - display name
# 2 - description
# 3 - default: if value >= 2, send e-mail by default
NOTICE_TYPES = (
    (
        'new_follower',
        _('A user is following you'),
        _('Your new images will be notified to them'),
        2
    ),
    (
        'follow_success',
        _('You are now following'),
        _('Their new images will be notified to you'),
        0
    ),
    (
        'unfollow_success',
        _('You are not following anymore'),
        _('Their new images will not be notified to you anymore'),
        0
    ),
    (
        'new_image',
        _('New image'),
        _('A user you follow has published a new image'),
        2
    ),
    (
        'attention_request',
        _('Attention request'),
        _('A user wants to bring an image to your attention'),
        2
    ),
    (
        'new_image_revision',
        _('New image revision'),
        _('A user you follow has uploaded a new image revision'),
        2
    ),
    (
        'image_ready',
        _('Image ready'),
        _('The image has been stored'),
        0
    ),
    (
        'image_solved',
        _('Image solved'),
        _('Plate solving the image has succeeded'),
        2
    ),
    (
        'image_not_solved',
        _('Image not solved'),
        _('Plate solving the image has failed'),
        2
    ),
    (
        'request_fulfilled',
        _('Request fulfilled'),
        _('The user has fulfilled your request'),
        2
    ),
    (
        'image_deleted',
        _('Image deleted'),
        _('Your image has been successfully deleted'),
        0
    ),
)


def create_notice_types(app, created_models, verbosity, **kwargs):
    for notice_type in NOTICE_TYPES:
        notification.create_notice_type(notice_type[0],
                                        notice_type[1],
                                        notice_type[2],
                                        notice_type[3])


signals.post_syncdb.connect(create_notice_types, sender=notification)

