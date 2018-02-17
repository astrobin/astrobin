# Django
from django.core.management import call_command

# Third party
from celery import shared_task


@shared_task()
def purge_old_notifications():
    call_command("purge_old_notifications")

