from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from persistent_messages.models import Message


class Command(BaseCommand):
    help = "Purges all read notification messages older than one week, and all unread ones older than 6 months"

    def handle(self, *args, **options):
        unread = Message.objects.filter(
            read=False,
            created__lt=datetime.now() - timedelta(30 * 6)
        )

        read = Message.objects.filter(
            read=True,
            created__lt=datetime.now() - timedelta(7)
        )

        unread.delete()
        read.delete()
