import datetime

from django.contrib.auth.models import User
from django.test import TransactionTestCase
from django_bouncy.models import Bounce, Complaint
from notification.models import NoticeType

from astrobin_apps_notifications.backends import EmailBackend


class EmailBackendTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user",
            email="user@test.com",
            password="password")
        self.notice_type = NoticeType.objects.get(label="test_notification")

    def tearDown(self):
        self.user.delete()

    def test_can_send_with_bounce(self):
        bounce = Bounce.objects.create(
            hard=True,
            bounce_type="Permanent",
            address=self.user.email,
            mail_timestamp=datetime.datetime.now()
        )

        self.assertFalse(EmailBackend(1).can_send(self.user, self.notice_type))

        bounce.delete()

    def test_can_send_with_complaint(self):
        complaint = Complaint.objects.create(
            address=self.user.email,
            mail_timestamp=datetime.datetime.now()
        )

        self.assertFalse(EmailBackend(1).can_send(self.user, self.notice_type))

        complaint.delete()

    def test_can_send_to_deleted_user(self):
        self.user.userprofile.deleted = datetime.datetime.now()
        self.assertFalse(EmailBackend(1).can_send(self.user, self.notice_type))
        self.user.userprofile.deleted = None

    def test_can_send(self):
        self.assertTrue(EmailBackend(1).can_send(self.user, self.notice_type))
