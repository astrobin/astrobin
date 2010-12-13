from django.core.management.base import BaseCommand
from astrobin.models import Subject

class Command(BaseCommand):
	help = "Creates the full list of NGC objects."

	def handle(self, *args, **options):
		for ngc in range(1, 110):
			s = Subject(name="NGC"+str(ngc))
			s.save()
