import logging

from celery import shared_task
from django.core.management import call_command

log = logging.getLogger(__name__)


@shared_task(time_limit=60, acks_late=True)
def fix_expired_subscriptions():
    call_command("fix_expired_subscriptions")


@shared_task(time_limit=60)
def send_expiration_notifications():
    call_command("send_expiring_subscription_notifications")
    call_command("send_expiring_subscription_autorenew_notifications")
    call_command("send_expired_subscription_notifications")
