# Django
from django.core.management import call_command

# Third party
from celery import shared_task


@shared_task()
def fix_expired_subscriptions():
    call_command("fix_expired_subscriptions")


@shared_task()
def send_expiration_notifications():
    call_command("send_expiration_notifications")
