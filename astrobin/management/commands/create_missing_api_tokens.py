# Django
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

# Third party apps
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = "Generates API tokens for users who lack one."

    def handle(self, *args, **options):
        for user in User.objects.all():
            token, created = Token.objects.get_or_create(user=user)
            print user, token
