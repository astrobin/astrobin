# Third party
from django_bouncy.models import Bounce
from gadjo.requestprovider.signals import get_request
from notification.backends import BaseBackend
from notification.backends.email import EmailBackend as BaseEmailBackend
import persistent_messages


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
            user = recipient)


class EmailBackend(BaseEmailBackend):
    def can_send(self, user, notice_type):
        can_send = super(EmailBackend, self).can_send(user, notice_type)
        bounces = Bounce.objects.filter(
            hard=True,
            bounce_type="Permanent",
            address=user.email)
        return can_send and not bounces.exists()
