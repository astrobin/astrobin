import csv
from django.core.management.base import BaseCommand
from astrobin.models import UserProfile


class Command(BaseCommand):
    help = "Export all user emails to a CSV file"

    def handle(self, *args, **options):
        profiles = UserProfile.objects.exclude(user__email = None)
        header = [['username', 'realname', 'email']]
        values = list(
            profiles.values_list('user__username', 'real_name', 'user__email'))
        data = header + values
        encoded = [(
            x[0],
            x[1].encode('utf-8') if x[1] is not None else '',
            x[2].encode('utf-8')) for x in data]

        with open('emails.csv', 'w') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerows(encoded)

