from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

import persistent_messages


class Command(BaseCommand):
    help = "Sends a message to all users."

    def handle(self, *args, **options):
        if len(args) < 2:
            print("Need two arguments: subject and body.")

        subject = args[0]
        body = args[1]
        sender = UserProfile.objects.get(user__username='astrobin').user

        for recipient in User.objects.all():
            if recipient.username != 'astrobin':
                persistent_messages.add_message_without_storage(
                    recipient,
                    sender,
                    persistent_messages.SUCCESS,
                    body,
                    subject = subject)
