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
        _('You are now following'),
        _('Their new images will be notified to you'))

    notification.create_notice_type(
        'unfollow_success',
        _('You are not following anymore'),
        _('Their new images will not be notified to you anymore'))

    notification.create_notice_type(
        'new_image',
        _('New image'),
        _('A user you follow has published a new image'))

    notification.create_notice_type(
        'attention_request',
        _('Attention request'),
        _('A user wants to bring an image to your attention'))

    notification.create_notice_type(
        'new_image_revision',
        _('New image revision'),
        _('A user you follow has uploaded a new image revision'))

    notification.create_notice_type(
        'image_ready',
        _('Image ready'),
        _('The image has been stored'))

    notification.create_notice_type(
        'image_solved',
        _('Image solved'),
        _('Plate solving the image has succeeded'))

    notification.create_notice_type(
        'image_not_solved',
        _('Image not solved'),
        _('Plate solving the image has failed'))

    notification.create_notice_type(
        'request_fulfilled',
        _('Request fulfilled'),
        _('The user has fulfilled your request'))

    notification.create_notice_type(
        'image_deleted',
        _('Image deleted'),
        _('Your image has been successfully deleted'))


signals.post_syncdb.connect(create_notice_types, sender=notification)

