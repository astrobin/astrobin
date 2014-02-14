from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from rawdata.models import RawImage
from rawdata.tasks import index_raw_image


class Command(BaseCommand):
    help = "Rebuilds the raw data index for a specific user"

    def handle(self, *args, **options):
        if len(args) == 0:
            print "Usage: rebuild_rawdata_index <username>"
            return

        username = args[0]
        try:
            user = User.objects.get(username = username)
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

