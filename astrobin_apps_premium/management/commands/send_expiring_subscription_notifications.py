from datetime import date

from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from subscription.models import UserSubscription

from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_premium.services.premium_service import SubscriptionName


class Command(BaseCommand):
    help = "Send a notification to user when their premium subscription expires in one week."

    def handle(self, *args, **kwargs):
        user_subscriptions = UserSubscription.objects.filter(
            subscription__name__in=[
                SubscriptionName.LITE_CLASSIC.value,
                SubscriptionName.PREMIUM_CLASSIC.value,
                SubscriptionName.LITE_2020.value,
                SubscriptionName.PREMIUM_2020.value,
                SubscriptionName.ULTIMATE_2020.value,
            ],
            active=True,
            expires=date.today() + relativedelta(weeks=1)
        )

        for user_subscription in user_subscriptions:
            push_notification(
                [user_subscription.user], None, 'expiring_subscription', {
                    'user_subscription': user_subscription,
                    'url': 'https://app.astrobin.com/subscriptions/view'
                }
            )
