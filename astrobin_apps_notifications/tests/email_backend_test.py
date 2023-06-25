import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TransactionTestCase
from django_bouncy.models import Bounce, Complaint
from notification.models import NoticeType

from astrobin.tests.generators import Generators
from astrobin_apps_notifications.backends import EmailBackend


class EmailBackendTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="user",
            email="user@test.com",
            password="password")
        self.user.userprofile.last_seen = datetime.datetime.now()
        self.user.userprofile.save()
        self.notice_type = NoticeType.objects.get(label="test_notification")

    def tearDown(self):
        self.user.delete()

    def test_can_send_with_hard_bounce(self):
        Bounce.objects.create(
            hard=True,
            bounce_type="Permanent",
            address=self.user.email,
            mail_timestamp=datetime.datetime.now()
        )

        self.assertFalse(EmailBackend(1).can_send(self.user, self.notice_type))

    def test_can_send_with_two_soft_bounces(self):
        Bounce.objects.create(
            hard=False,
            bounce_type="Transient",
            address=self.user.email,
            mail_timestamp=datetime.datetime.now()
        )

        Bounce.objects.create(
            hard=False,
            bounce_type="Transient",
            address=self.user.email,
            mail_timestamp=datetime.datetime.now()
        )

        self.assertTrue(EmailBackend(1).can_send(self.user, self.notice_type))

    def test_can_send_with_three_soft_bounces(self):
        Bounce.objects.create(
            hard=False,
            bounce_type="Transient",
            address=self.user.email,
            mail_timestamp=datetime.datetime.now()
        )

        Bounce.objects.create(
            hard=False,
            bounce_type="Transient",
            address=self.user.email,
            mail_timestamp=datetime.datetime.now()
        )

        Bounce.objects.create(
            hard=False,
            bounce_type="Transient",
            address=self.user.email,
            mail_timestamp=datetime.datetime.now()
        )

        self.assertFalse(EmailBackend(1).can_send(self.user, self.notice_type))

    def test_can_send_with_complaint(self):
        Complaint.objects.create(
            address=self.user.email,
            mail_timestamp=datetime.datetime.now()
        )

        self.assertFalse(EmailBackend(1).can_send(self.user, self.notice_type))

    def test_can_send_to_deleted_user(self):
        self.user.userprofile.deleted = datetime.datetime.now()
        self.assertFalse(EmailBackend(1).can_send(self.user, self.notice_type))
        self.user.userprofile.deleted = None

    def test_can_send_inactive_user(self):
        self.user.userprofile.last_seen = datetime.datetime.now() - datetime.timedelta(days=91)
        self.assertFalse(EmailBackend(1).can_send(self.user, self.notice_type))
        self.user.userprofile.last_seen = datetime.datetime.now()

    def test_can_send(self):
        self.assertTrue(EmailBackend(1).can_send(self.user, self.notice_type))

    @patch('astrobin_apps_notifications.backends.send_mail')
    def test_deliver_with_shadow_ban(self, send_mail):
        sender: User = Generators.user()
        user: User = Generators.user()

        user.userprofile.shadow_bans.add(sender.userprofile)

        EmailBackend(1).deliver(user, sender, self.notice_type, {})

        send_mail.assert_not_called()

    @patch('astrobin_apps_notifications.backends.send_mail')
    def test_deliver(self, send_mail):
        sender: User = Generators.user()
        user: User = Generators.user()

        EmailBackend(1).deliver(user, sender, self.notice_type, {})

        send_mail.assert_called()
