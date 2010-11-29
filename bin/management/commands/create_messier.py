from django.core.management.base import BaseCommand
from bin.models import Subject

class Command(BaseCommand):
	help = "Creates the full list of Messier objects."

	def handle(self, *args, **options):
		for m in range(1, 110):
			s = Subject(name="M"+str(m))
			s.save()
