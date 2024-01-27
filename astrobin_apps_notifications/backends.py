import logging
from datetime import datetime, timedelta

import persistent_messages
from django.conf import settings
from django.core.mail import send_mail
from django.template import TemplateDoesNotExist
from django.template.loader import get_template, render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django_bouncy.models import Bounce, Complaint
from notification.backends import BaseBackend
from notification.backends.email import EmailBackend as BaseEmailBackend
from persistent_messages.models import Message

from astrobin_apps_users.services import UserService

log = logging.getLogger(__name__)


class PersistentMessagesBackend(BaseBackend):
    spam_sensitivity = 1

    def deliver(self, recipient, sender, notice_type, extra_context):
        context = self.default_context()
        context.update(extra_context)

        if UserService(recipient).shadow_bans(sender):
            log.debug("On-site notice %s not sent because of shadow ban: %s -> %s" % (notice_type, recipient, sender))
            return

        template = 'notice.html'
        message = self.get_formatted_messages([template], notice_type.label, context)[template]
        level = persistent_messages.INFO
        persistent_message = Message(user=recipient, from_user=sender, level=level, message=message)
        persistent_message.save()


class EmailBackend(BaseEmailBackend):
    def can_send(self, user, notice_type):
        hard_bounces = Bounce.objects.filter(
            hard=True,
            bounce_type="Permanent",
            address=user.email)
        soft_bounces = Bounce.objects.filter(
            hard=False,
            bounce_type="Transient",
            address=user.email,
            created_at__gte=datetime.now() - timedelta(days=7))
        complaints = Complaint.objects.filter(
            address=user.email)
        deleted = user.userprofile.deleted is not None
        ignored = 'ASTROBIN_IGNORE' in user.email
        last_seen = user.userprofile.last_seen or user.last_login
        inactive = last_seen is None or last_seen < datetime.now() - timedelta(days=180)

        if deleted or hard_bounces.exists() or soft_bounces.count() > 2 or complaints or ignored or inactive:
            return False

        return super(EmailBackend, self).can_send(user, notice_type)

    def deliver(self, recipient, sender, notice_type, extra_context):
        context = self.default_context()
        context.update({
            "recipient": recipient,
            "sender": sender,
            "notice": ugettext(notice_type.display),
        })
        context.update(extra_context)

        if UserService(recipient).shadow_bans(sender):
            log.debug("Email notice %s not sent because of shadow ban: %s -> %s" % (notice_type, recipient, sender))
            return

        messages = self.get_formatted_messages((
            "short.txt",
            "full.txt",
            "full.html"
        ), notice_type.label, context)

        subject = "".join(render_to_string("notification/email_subject.txt", dict(context, **{
            "message": messages["short.txt"],
        })).splitlines())

        body = render_to_string("notification/email_body.txt", dict(context, **{
            "message": messages["full.txt"]
        }))

        try:
            get_template("notification/%s/full.html" % notice_type.label)
            message = messages["full.html"]
        except TemplateDoesNotExist:
            message = messages["full.txt"]

        html_body = render_to_string("notification/email_body.html", dict(context, **{
            "message": mark_safe(str(message))
        }))

        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_DEV_RECIPIENT if settings.SEND_EMAILS == 'dev' else recipient.email],
            html_message=html_body)
