from datetime import datetime, timedelta

from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from mock import patch

from astrobin.admin import BroadcastEmailAdmin
from astrobin.models import BroadcastEmail


class BroadcastEmailAdminTest(TestCase):
    @patch("django.core.mail.EmailMessage.send")
    def test_submit_premium_offer_discount_no_users(self, sendMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))

        sendMock.assert_not_called()

    @patch("django.core.mail.EmailMessage.send")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_premium_offer_discount(self, messageUserMock, sendMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="discount", password="discount")
        user.userprofile.premium_offer = "premium_offer_discount_20"
        user.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user.userprofile.save()

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))

        sendMock.assert_called()
        self.assertEqual(1, sendMock.call_count)
        user.userprofile.refresh_from_db()
        self.assertIsNotNone(user.userprofile.premium_offer_sent)

    @patch("django.core.mail.EmailMessage.send")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_premium_offer_discount_two_users(self, messageUserMock, sendMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="discount", password="discount")
        user.userprofile.premium_offer = "premium_offer_discount_20"
        user.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user.userprofile.save()

        user2 = User.objects.create(username="discount2", password="discount")
        user2.userprofile.premium_offer = "premium_offer_discount_50"
        user2.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user2.userprofile.save()

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))

        sendMock.assert_called()
        self.assertEqual(2, sendMock.call_count)

        user.userprofile.refresh_from_db()
        user2.userprofile.refresh_from_db()
        self.assertIsNotNone(user.userprofile.premium_offer_sent)
        self.assertIsNotNone(user2.userprofile.premium_offer_sent)

    @patch("django.core.mail.EmailMessage.send")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_premium_offer_discount_already_sent_long_ago(self, messageUserMock, sendMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="discount", password="discount")
        user.userprofile.premium_offer = "premium_offer_discount_20"
        user.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user.userprofile.premium_offer_sent = datetime.now() - timedelta(days=31)
        user.userprofile.save()

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))

        sendMock.assert_called()
        self.assertEqual(1, sendMock.call_count)
        user.userprofile.refresh_from_db()
        self.assertTrue(user.userprofile.premium_offer_sent > datetime.now() - timedelta(minutes=1))

    @patch("django.core.mail.EmailMessage.send")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_premium_offer_discount_already_sent_too_recently(self, messageUserMock, sendMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="discount", password="discount")
        user.userprofile.premium_offer = "premium_offer_discount_20"
        user.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user.userprofile.premium_offer_sent = sent = datetime.now() - timedelta(days=20)
        user.userprofile.save()

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))

        sendMock.assert_not_called()
        user.userprofile.refresh_from_db()
        self.assertEqual(sent, user.userprofile.premium_offer_sent)
