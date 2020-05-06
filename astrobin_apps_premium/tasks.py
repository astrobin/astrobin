import logging
from datetime import date

from annoying.functions import get_object_or_None
from celery import shared_task
from django.core.management import call_command
from subscription.models import UserSubscription

from astrobin_apps_premium.models import DataLossCompensationRequest

log = logging.getLogger("apps")


@shared_task()
def fix_expired_subscriptions():
    call_command("fix_expired_subscriptions")


@shared_task()
def send_expiration_notifications():
    call_command("send_expiration_notifications")


@shared_task()
def reactivate_previous_subscription_when_ultimate_compensation_expires():
    expiring_ultimates = UserSubscription.objects.filter(
        subscription__name="AstroBin Ultimate 2020+",
        expires=date.today()
    )

    for ultimate_user_subscription in expiring_ultimates:
        compensation_request = get_object_or_None(
            DataLossCompensationRequest,
            user=ultimate_user_subscription.user,
            requested_compensation__in=(
                '1_MO_ULTIMATE',
                '3_MO_ULTIMATE',
                '6_MO_ULTIMATE'
            )
        )

        if compensation_request:
            previous_subscription = UserSubscription.objects.filter(
                user=ultimate_user_subscription.user,
                subscription__category__in=('premium', 'premium_autorenew'),
                expires__gt=date.today()
            ).exclude(
                subscription__name="AstroBin Ultimate 2020+"
            ).first()  # type: UserSubscription

            if previous_subscription:
                previous_subscription.subscribe()
                previous_subscription.active = True
                previous_subscription.save()
                ultimate_user_subscription.unsubscribe()
                log.debug(
                    "Reactivated subscription %s for user %s as Ultimate compensation expired" % (
                        previous_subscription.subscription.name,
                        previous_subscription.user.username
                    ))
