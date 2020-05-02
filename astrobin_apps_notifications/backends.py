import logging

import persistent_messages
from django.conf import settings
from django.core.mail import send_mail
from django.template import TemplateDoesNotExist
from django.template.loader import get_template, render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django_bouncy.models import Bounce, Complaint
from gadjo.requestprovider.signals import get_request
from notification.backends import BaseBackend
from notification.backends.email import EmailBackend as BaseEmailBackend

log = logging.getLogger('apps')


class PersistentMessagesBackend(BaseBackend):
    spam_sensitivity = 1

    def deliver(self, recipient, sender, notice_type, extra_context):
        try:
            request = get_request()
        except IndexError:
            # This may happen during unit testing
            return

        context = self.default_context()
        context.update(extra_context)
        messages = self.get_formatted_messages(
            ['notice.html'],
            notice_type.label, context)
        persistent_messages.add_message(
            request,
            persistent_messages.INFO,
            messages['notice.html'],
            user=recipient)


class EmailBackend(BaseEmailBackend):
    def can_send(self, user, notice_type):
        bounces = Bounce.objects.filter(
            hard=True,
            bounce_type="Permanent",
            address=user.email)
        complaints = Complaint.objects.filter(
            address=user.email)
        deleted = user.userprofile.deleted is not None

        if deleted or bounces or complaints:
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
            "message": mark_safe(unicode(message))
        }))

        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_DEV_RECIPIENT if settings.SEND_EMAILS == 'dev' else recipient.email],
            html_message=html_body)

        log.debug("Email sent to %s: %s" % (recipient.email, subject))
