from datetime import date, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from subscription.models import UserSubscription


class Command(BaseCommand):
    help = "Mark expired subscriptions as cancelled"

    def handle(self, *args, **options):
        UserSubscription.objects.filter(
            active=True,
            cancelled=False,
            expires__lt=date.today() - timedelta(settings.SUBSCRIPTION_GRACE_PERIOD + 1),
            subscription__recurrence_unit__isnull=False
        ).update(cancelled=True)
