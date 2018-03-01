from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from rawdata.models import RawImage
from rawdata.tasks import index_raw_image


class Command(BaseCommand):
    help = "Rebuilds the raw data index for a specific user"

    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, *args, **options):
        username = options['username']

        try:
            user = UserProfile.objects.get(user__username = username).user
        except User.DoesNotExist:
            print "User not found."
            return

        images = RawImage.objects.filter(user = user, indexed = False)
        for i in images:
            try:
                index_raw_image(i.id)
            except ValueError:
                print "File failed: %s" % i.original_filename
                continue

