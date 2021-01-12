import datetime

from django.contrib.auth.models import User
from django.test import TransactionTestCase
from django_bouncy.models import Bounce, Complaint, Delivery
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

    def test_can_send_with_hard_bounce(self):
        Bounce.objects.create(
            hard=True,
            bounce_type="Permanent",
            address=self.user.email,
            mail_timestamp=datetime.datetime.now()
        )

        self.assertFalse(EmailBackend(1).can_send(self.user, self.notice_type))

    def test_can_send_with_hard_bounce_followed_by_delivery(self):
        Bounce.objects.create(
            hard=True,
            bounce_type="Permanent",
            address=self.user.email,
            mail_timestamp=datetime.datetime.now() - datetime.timedelta(days=2)
        )

        Delivery.objects.create(
            address=self.user.email,
            mail_timestamp=datetime.datetime.now() - datetime.timedelta(days=1),
            delivered_time=datetime.datetime.now() - datetime.timedelta(days=1)
        )

        self.assertTrue(EmailBackend(1).can_send(self.user, self.notice_type))

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


    def test_can_send_with_three_soft_bounces_but_one_of_them_is_after_a_delivery(self):
        Bounce.objects.create(
            hard=False,
            bounce_type="Transient",
            address=self.user.email,
            mail_timestamp=datetime.datetime.now() - datetime.timedelta(days=4)
        )

        Bounce.objects.create(
            hard=False,
            bounce_type="Transient",
            address=self.user.email,
            mail_timestamp=datetime.datetime.now() - datetime.timedelta(days=3)
        )

        Delivery.objects.create(
            address=self.user.email,
            mail_timestamp=datetime.datetime.now() - datetime.timedelta(days=2),
            delivered_time=datetime.datetime.now() - datetime.timedelta(days=2)
        )

        Bounce.objects.create(
            hard=False,
            bounce_type="Transient",
            address=self.user.email,
            mail_timestamp=datetime.datetime.now() - datetime.timedelta(days=1)
        )

        self.assertTrue(EmailBackend(1).can_send(self.user, self.notice_type))

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

    def test_can_send(self):
        self.assertTrue(EmailBackend(1).can_send(self.user, self.notice_type))
