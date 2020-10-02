from datetime import date, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from subscription.models import UserSubscription


class Command(BaseCommand):
    help = "Delete expired subscriptions"

    def handle(self, *args, **options):
        UserSubscription.objects.filter(
            active=True,
            cancelled=False,
            expires__lt=date.today() - timedelta(settings.SUBSCRIPTION_GRACE_PERIOD)
        ).update(cancelled=True)
