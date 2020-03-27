from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django_bouncy.models import Bounce

from astrobin.models import DataDownloadRequest
from astrobin.tasks import expire_download_data_requests, delete_inactive_bounced_accounts
from astrobin.tests.generators import Generators


class TaskTest(TestCase):
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_delete_inactive_bounced_accounts(self):
        user = User.objects.create_user(
            'test', 'test@test.com', 'password')
        bounce = Bounce.objects.create(
            hard=True,
            bounce_type="Permanent",
            address="test@test.com",
            mail_timestamp=datetime.now())

        user.is_active = False
        user.save()

        delete_inactive_bounced_accounts.apply()

        self.assertFalse(User.objects.filter(username="test").exists())
        self.assertFalse(Bounce.objects.filter(address="test@test.com").exists())


    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_expire_download_data_requests(self):
        old_request = DataDownloadRequest.objects.create(
            user = Generators.user(),
        )

        old_request.created = datetime.now() - timedelta(days=8)
        old_request.save()

        recent_request = DataDownloadRequest.objects.create(
            user=Generators.user(),
        )

        expire_download_data_requests.apply()

        self.assertEquals("EXPIRED", DataDownloadRequest.objects.get(pk=old_request.pk).status)
        self.assertEquals("PENDING", DataDownloadRequest.objects.get(pk=recent_request.pk).status)
