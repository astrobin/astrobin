# Django
import persistent_messages
from django.conf import settings
from django.core.mail import send_mail
from django.template import TemplateDoesNotExist
from django.template.loader import get_template, render_to_string
from django.utils.translation import ugettext
# Third party
from django_bouncy.models import Bounce
from gadjo.requestprovider.signals import get_request
from notification.backends import BaseBackend
from notification.backends.email import EmailBackend as BaseEmailBackend


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
        messages = self.get_formatted_messages(['notice.html'],
                                               notice_type.label, context)
        persistent_messages.add_message(
            request,
            persistent_messages.INFO,
            messages['notice.html'],
            user=recipient)


class EmailBackend(BaseEmailBackend):
    def can_send(self, user, notice_type):
        can_send = super(EmailBackend, self).can_send(user, notice_type)
        bounces = Bounce.objects.filter(
            hard=True,
            bounce_type="Permanent",
            address=user.email)
        return can_send and not bounces.exists()

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

        subject = "".join(render_to_string("notification/email_subject.txt", {
            "message": messages["short.txt"],
        }, context).splitlines())

        body = render_to_string("notification/email_body.txt", {
            "message": messages["full.txt"],
        }, context)

        try:
            html_template = get_template(
                "notification/%s/full.html" % notice_type.label)
            message = messages["full.html"]
        except TemplateDoesNotExist:
            message = messages["full.txt"]

        html_body = render_to_string("notification/email_body.html", {
            "message": message
        }, context)

        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [recipient.email],
            html_message=html_body)
