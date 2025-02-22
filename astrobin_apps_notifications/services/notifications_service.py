from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMessage


class NotificationContext:
    SUBSCRIPTIONS = "subscriptions"
    API = "api"
    AUTHENTICATION = "authentication"
    USER = "user"
    GROUPS = "groups"
    FORUM = "forum"
    MARKETPLACE = "marketplace"
    IOTD = "iotd"
    EQUIPMENT = "equipment"
    IMAGE = "image"


class NotificationsService:
    @staticmethod
    def email_superusers(subject, body):
        message = {
            'from_email': settings.SERVER_EMAIL,
            'to': [x.email for x in User.objects.filter(is_superuser=True)],
            'subject': subject,
            'body': body
        }
        EmailMessage(**message).send(fail_silently=False)
