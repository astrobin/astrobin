import csv
import datetime
from optparse import make_option

from django.core.management.base import BaseCommand

from astrobin.models import UserProfile


class Command(BaseCommand):
    help = "Export all user emails to a CSV file"
    option_list = BaseCommand.option_list + (
        make_option('--since',
                    help="A starting date in the yyyy-mm-dd format",
                    dest="since",
                    default=False),
    )

    def handle(self, *args, **options):
        def default_since():
            return datetime.datetime.fromtimestamp(0)

        since = options.get('since')
        if since == False:
            since = default_since()

        try:
            since = datetime.datetime.strptime(since, "%Y-%m-%d")
        except:
            since = default_since()

        profiles = UserProfile.objects \
            .filter(user__date_joined__gte=since) \
            .exclude(user__email=None)
        header = [['username', 'realname', 'email', 'joined']]
        values = list(
            profiles.values_list(
                'user__username',
                'real_name',
                'user__email',
                'user__date_joined'))
        data = header + values
        encoded = [(
            x[0],
            x[1].encode('utf-8') if x[1] is not None else '',
            x[2].encode('utf-8'),
            x[3]) for x in data
        ]

        filename = 'emails_since_%s.csv' % \
                   datetime.datetime.strftime(since, "%Y_%m_%d")
        with open(filename, 'w') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerows(encoded)
