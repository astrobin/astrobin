# Python
from datetime import datetime, timedelta

# Django
from django.core.management.base import BaseCommand

# This app
from rawdata.models import TemporaryArchive


class Command(BaseCommand):
    help = "Delete temporary archives older than the specified number of days (defaul = 2)."

    def handle(self, *args, **options):
        days = 2
        if args:
            days = args[0]

        archives = TemporaryArchive.objects.filter(
            created__lte=datetime.now() - timedelta(days=days))

        for archive in archives:
            print "Deleting archive: %s" % archive
            archive.delete()
            archive.file.storage.delete(archive.file.path)
