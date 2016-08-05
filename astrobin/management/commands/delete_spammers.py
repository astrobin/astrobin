from django.core.management.base import BaseCommand

from astrobin.models import Image

class Command(BaseCommand):
    help = "Delete accounts of people with images in the spam list."

    def handle(self, *args, **options):
        spam_images = Image.all_objects.filter(moderator_decision = 2)
        for image in spam_images:
            print "Deleting user %s" % image.user
            image.user.delete()
