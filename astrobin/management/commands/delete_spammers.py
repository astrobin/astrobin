from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from astrobin.models import Image

class Command(BaseCommand):
    help = "Delete accounts of people with images in the spam list."

    def handle(self, *args, **options):
	spammers = []
        spam = Image.all_objects.filter(moderator_decision = 2)
        for image in spam:
            if image.user not in spammers:
                spammers.append(image.user)

	for spammer in spammers:
            print "Deleting spammer %s" % spammer
            try:
                spammer.delete()
            except User.DoesNotExist:
                pass
