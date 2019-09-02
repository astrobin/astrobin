from datetime import datetime, timedelta

from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from django.test import TestCase, RequestFactory
from django.utils import timezone
from mock import patch
from subscription.models import Subscription, UserSubscription

from astrobin.admin import BroadcastEmailAdmin
from astrobin.models import BroadcastEmail


class BroadcastEmailAdminPremiumOfferTest(TestCase):
    @patch("astrobin.tasks.send_broadcast_email.delay")
    def test_submit_premium_offer_discount_no_users(self, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_premium_offer_discount(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="discount", password="discount", email="email@email.com")
        user.userprofile.premium_offer = "premium_offer_discount_20"
        user.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user.userprofile.receive_marketing_and_commercial_material = True
        user.userprofile.save()

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))

        args, kwargs = taskMock.call_args
        taskMock.assert_called()
        self.assertEquals(["email@email.com"], list(args[1]))
        self.assertEqual(1, taskMock.call_count)
        user.userprofile.refresh_from_db()
        self.assertIsNotNone(user.userprofile.premium_offer_sent)

    @patch("astrobin.tasks.send_broadcast_email.delay")
    def test_submit_premium_offer_discount_no_marketing_emails(self, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="discount", password="discount")
        user.userprofile.premium_offer = "premium_offer_discount_20"
        user.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user.userprofile.save()

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    def test_submit_premium_offer_discount_already_premium(self, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())


        user = User.objects.create(username="discount", password="discount")
        user.userprofile.premium_offer = "premium_offer_discount_20"
        user.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user.userprofile.receive_marketing_and_commercial_material = True
        user.userprofile.save()

        group, created = Group.objects.get_or_create(name="astrobin_premium")
        subscription, created = Subscription.objects.get_or_create(
            name="AstroBin Premium",
            price=1,
            group=group,
            category="premium")
        user_subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            subscription=subscription)

        user_subscription.subscribe()

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_premium_offer_discount_already_premium_but_expired(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="discount", password="discount", email="email@email.com")
        user.userprofile.premium_offer = "premium_offer_discount_20"
        user.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user.userprofile.receive_marketing_and_commercial_material = True
        user.userprofile.save()

        group, created = Group.objects.get_or_create(name="astrobin_premium")
        subscription, created = Subscription.objects.get_or_create(
            name="AstroBin Premium",
            price=1,
            group=group,
            category="premium")
        user_subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            subscription=subscription)

        user_subscription.subscribe()

        user_subscription.expires = timezone.now() - timedelta(days=1)
        user_subscription.save()

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))
        args, kwargs = taskMock.call_args
        taskMock.assert_called()
        self.assertEquals(["email@email.com"], list(args[1]))

    @patch("astrobin.tasks.send_broadcast_email.delay")
    def test_submit_premium_offer_discount_already_lite(self, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="discount", password="discount")
        user.userprofile.premium_offer = "premium_offer_discount_20"
        user.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user.userprofile.receive_marketing_and_commercial_material = True
        user.userprofile.save()

        group, created = Group.objects.get_or_create(name="astrobin_premium")
        subscription, created = Subscription.objects.get_or_create(
            name="AstroBin Lite",
            price=1,
            group=group,
            category="premium")
        user_subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            subscription=subscription)

        user_subscription.subscribe()

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_premium_offer_discount_already_premium_with_discount(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="discount", password="discount")
        user.userprofile.premium_offer = "premium_offer_discount_20"
        user.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user.userprofile.receive_marketing_and_commercial_material = True
        user.userprofile.save()

        group, created = Group.objects.get_or_create(name="astrobin_premium")
        subscription, created = Subscription.objects.get_or_create(
            name="AstroBin Premium 30% discount",
            price=1,
            group=group,
            category="premium_offer_discount_30")
        user_subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            subscription=subscription)

        user_subscription.subscribe()

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_premium_offer_discount_two_users(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="discount", password="discount", email="email@email.com")
        user.userprofile.premium_offer = "premium_offer_discount_20"
        user.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user.userprofile.receive_marketing_and_commercial_material = True
        user.userprofile.save()

        user2 = User.objects.create(username="discount2", password="discount", email="email2@email.com")
        user2.userprofile.premium_offer = "premium_offer_discount_50"
        user2.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user2.userprofile.receive_marketing_and_commercial_material = True
        user2.userprofile.save()

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))

        args, kwargs = taskMock.call_args
        taskMock.assert_called()
        self.assertEquals(["email@email.com", "email2@email.com"], list(args[1]))
        user.userprofile.refresh_from_db()
        user2.userprofile.refresh_from_db()
        self.assertIsNotNone(user.userprofile.premium_offer_sent)
        self.assertIsNotNone(user2.userprofile.premium_offer_sent)

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_premium_offer_discount_already_sent_long_ago(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="discount", password="discount", email="email@email.com")
        user.userprofile.premium_offer = "premium_offer_discount_20"
        user.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user.userprofile.premium_offer_sent = datetime.now() - timedelta(days=31)
        user.userprofile.receive_marketing_and_commercial_material = True
        user.userprofile.save()

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))

        args, kwargs = taskMock.call_args
        taskMock.assert_called()
        self.assertEquals(["email@email.com"], list(args[1]))
        user.userprofile.refresh_from_db()
        self.assertTrue(user.userprofile.premium_offer_sent > datetime.now() - timedelta(minutes=1))

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_premium_offer_discount_already_sent_too_recently(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="discount", password="discount")
        user.userprofile.premium_offer = "premium_offer_discount_20"
        user.userprofile.premium_offer_expiration = datetime.now() + timedelta(days=1)
        user.userprofile.premium_offer_sent = sent = datetime.now() - timedelta(days=20)
        user.userprofile.receive_marketing_and_commercial_material = True
        user.userprofile.save()

        admin.submit_premium_offer_discount(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()
        user.userprofile.refresh_from_db()
        self.assertEqual(sent, user.userprofile.premium_offer_sent)
