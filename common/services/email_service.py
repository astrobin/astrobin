from datetime import datetime, timedelta

from django.db.models import QuerySet
from django_bouncy.models import Delivery, Bounce, Complaint


class EmailService:
    @staticmethod
    def get_latest_delivery(address):
        # type: (str) -> Delivery

        return Delivery.objects.filter(address=address).order_by('-delivered_time').first()

    @staticmethod
    def hard_bounces(address):
        # type: (str) -> QuerySet

        latest_delivery = EmailService.get_latest_delivery(address)

        hard_bounces = Bounce.objects.filter(
            hard=True,
            bounce_type="Permanent",
            address=address)

        if latest_delivery:
            hard_bounces = hard_bounces.filter(mail_timestamp__gt=latest_delivery.delivered_time)

        return hard_bounces

    @staticmethod
    def soft_bounces(address):
        # type: (str) -> QuerySet

        latest_delivery = EmailService.get_latest_delivery(address)

        soft_bounces = Bounce.objects.filter(
            hard=False,
            bounce_type="Transient",
            address=address,
            mail_timestamp__gte=datetime.now() - timedelta(days=7))

        if latest_delivery:
            soft_bounces = soft_bounces.filter(mail_timestamp__gt=latest_delivery.delivered_time)

        return soft_bounces

    @staticmethod
    def complaints(address):
        # type: (str) -> QuerySet

        return Complaint.objects.filter(address=address)
