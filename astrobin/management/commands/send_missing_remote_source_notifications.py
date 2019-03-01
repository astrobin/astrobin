from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from astrobin_apps_notifications.utils import push_notification
from astrobin.models import Image


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for user in User.objects.all():
            images = Image.objects.filter(
                user=user,
                data_source__in=["OWN_REMOTE", "AMATEUR_HOSTING"],
                remote_source=None)

            if images.count() > 0:
                push_notification([user], 'missing_remote_source', {
                    'BASE_URL': settings.BASE_URL,
                    'images': images
                })
