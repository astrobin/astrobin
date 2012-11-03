from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from zinnia.models import Entry

from astrobin.notifications import push_notification

class Command(BaseCommand):
    help = "Notifies all users about most recent blog entry."

    def handle(self, *args, **options):
        entry = Entry.objects.all()[0]
        push_notification(
            User.objects.all(),
            'new_blog_entry',
            {
                'object': entry.title,
                'object_url': entry.get_absolute_url()
            }
        )
