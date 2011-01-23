from django.conf import settings
from django.db.models import signals
from django.utils.translation import ugettext_noop as _

if 'notification' in settings.INSTALLED_APPS:
    from notification import models as notification

    def create_notice_types(app, created_models, verbosity, **kwargs):
        notification.create_notice_type('new_follower', _('A user is following you'), _('Your new images will be notified to them'))
        notification.create_notice_type('follow_success', _('You are now folling a user'), _('Their new images will be notified to you'))

    signals.post_syncdb.connect(create_notice_types, sender=notification)
else:
    print 'Skipping creation of NoticeTypes as notification app not found'

