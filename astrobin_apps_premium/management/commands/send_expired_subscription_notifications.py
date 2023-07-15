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
           "is expired."

    def handle(self, *args, **kwargs):
        user_subscriptions = UserSubscription.objects.filter(
            subscription__name__in = [
                SubscriptionName.LITE_CLASSIC.value,
                SubscriptionName.PREMIUM_CLASSIC.value,
                SubscriptionName.LITE_CLASSIC_AUTORENEW.value,
                SubscriptionName.PREMIUM_CLASSIC_AUTORENEW.value,
                SubscriptionName.LITE_2020.value,
                SubscriptionName.LITE_2020_AUTORENEW_MONTHLY.value,
                SubscriptionName.LITE_2020_AUTORENEW_YEARLY.value,
                SubscriptionName.PREMIUM_2020.value,
                SubscriptionName.PREMIUM_2020_AUTORENEW_MONTHLY.value,
                SubscriptionName.PREMIUM_2020_AUTORENEW_YEARLY.value,
                SubscriptionName.ULTIMATE_2020.value,
                SubscriptionName.ULTIMATE_2020_AUTORENEW_MONTHLY.value,
                SubscriptionName.ULTIMATE_2020_AUTORENEW_YEARLY.value,
            ],
            active=True,
            expires = datetime.now() - timedelta(days=2))

        for user_subscription in user_subscriptions:
            push_notification([user_subscription.user], None, 'expired_subscription', {
                'user_subscription': user_subscription,
                'url': 'https://app.astrobin.com/subscriptions/options'
            })
