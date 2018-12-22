from datetime import date
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from astrobin_apps_notifications.utils import push_notification
from astrobin.models import Image


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # To avoid sending too many emails, only get the users that joined on the same day of the month as today. By
        # running this script daily, you get to spread all these emails over a period of 30 days, and each user doesn't
        # get it more often than once a month.
        for user in User.objects.filter(date_joined__day = date.today().day):
            images = Image.objects.filter(user=user, data_source="UNSET")

            if images.count() > 0:
                push_notification([user], 'missing_data_source', {
                    'BASE_URL': settings.BASE_URL,
                    'images': images
                })
