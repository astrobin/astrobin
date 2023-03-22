# Python
from datetime import datetime, timedelta

# Django
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse

# Third party
from subscription.models import UserSubscription

# AstroBin
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_premium.services.premium_service import SubscriptionName


class Command(BaseCommand):
    help = "Send a notification to user when their premium subscription " +\
           "expires in one week."

    def handle(self, *args, **kwargs):
        user_subscriptions = UserSubscription.objects\
            .filter(
                subscription__name__in = [
                    SubscriptionName.LITE_CLASSIC,
                    SubscriptionName.PREMIUM_CLASSIC,
                    SubscriptionName.LITE_2020,
                    SubscriptionName.PREMIUM_2020,
                    SubscriptionName.ULTIMATE_2020,
                ],
            active=True,
            expires = datetime.now() + timedelta(days = 7))\
            .exclude(subscription__recurrence_unit = None)

        for user_subscription in user_subscriptions:
            push_notification([user_subscription.user], None, 'expiring_subscription', {
                'user_subscription': user_subscription,
                'url': 'https://app.astrobin.com/subscriptions/options'
            })
