from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

import persistent_messages
from zinnia.models import Entry


class Command(BaseCommand):
    help = "Notifies all users about most recent blog entry."

    def handle(self, *args, **options):
        entry = Entry.objects.all()[0]
        for u in User.objects.all():
            m = persistent_messages.models.Message(
                user = u,
                from_user = User.objects.get(username = 'astrobin'),
                message = '<a href="' + entry.get_absolute_url() + '">New blog entry: <strong>' + entry.title + '</strong></a>',
                level = persistent_messages.INFO,
            )
            m.save()
