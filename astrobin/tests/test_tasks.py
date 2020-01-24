# Django
from django.test import TestCase, override_settings
from django.utils import timezone

# AstroBin
from astrobin.tasks import *


class TaskTest(TestCase):
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_delete_inactive_bounced_accounts(self):
        user = User.objects.create_user(
            'test', 'test@test.com', 'password')
        bounce = Bounce.objects.create(
            hard=True,
            bounce_type="Permanent",
            address="test@test.com",
            mail_timestamp=timezone.now())

        user.is_active = False
        user.save()

        delete_inactive_bounced_accounts.apply()

        self.assertFalse(User.objects.filter(username="test").exists())
        self.assertFalse(Bounce.objects.filter(address="test@test.com").exists())

