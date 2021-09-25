import logging
from datetime import date

from annoying.functions import get_object_or_None
from celery import shared_task
from django.core.management import call_command
from subscription.models import UserSubscription

log = logging.getLogger("apps")


@shared_task(time_limit=60, acks_late=True)
def fix_expired_subscriptions():
    call_command("fix_expired_subscriptions")


@shared_task(time_limit=60)
def send_expiration_notifications():
    call_command("send_expiring_subscription_notifications")
    call_command("send_expiring_subscription_autorenew_notifications")
    call_command("send_expired_subscription_notifications")
