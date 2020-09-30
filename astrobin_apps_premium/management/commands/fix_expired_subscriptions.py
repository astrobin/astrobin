from datetime import date, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from subscription.models import UserSubscription


class Command(BaseCommand):
    help = "Delete expired subscriptions"

    def handle(self, *args, **options):
        UserSubscription.objects.filter(
            subscription__name__in=[
                "AstroBin Ultimate 2020+",
                "AstroBin Premium 2020+",
                "AstroBin Lite 2020+",
                "AstroBin Premium",
                "AstroBin Lite",
            ],
            expires__lt=date.today() - timedelta(days=settings.SUBSCRIPTION_GRACE_PERIOD + 1)
        ).delete()

        # Extra grace period for auto-renewing subscriptions, to give PayPal some time to retry.

        UserSubscription.objects.filter(
            subscription__name__in=[
                "AstroBin Premium (autorenew)",
                "AstroBin Lite (autorenew)",
            ],
            expires__lt=date.today() - timedelta(days=settings.SUBSCRIPTION_GRACE_PERIOD + 7)
        ).delete()
