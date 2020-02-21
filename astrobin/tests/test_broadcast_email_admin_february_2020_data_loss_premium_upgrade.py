from datetime import date

from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from django.test import TestCase, RequestFactory
from mock import patch
from subscription.models import UserSubscription, Subscription

from astrobin.admin import BroadcastEmailAdmin
from astrobin.models import BroadcastEmail


class BroadcastEmailAdminFebruary2020DataLossPremiumUpgradeTest(TestCase):
    @patch("astrobin.tasks.send_broadcast_email.delay")
    def test_submit_february_2020_data_loss_premium_upgrade_no_users(self, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        admin.submit_february_2020_data_loss_premium_upgrade(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_february_2020_data_loss_premium_upgrade_no_premium(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        User.objects.create(username="test", password="test")

        admin.submit_february_2020_data_loss_premium_upgrade(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_february_2020_data_loss_premium_upgrade_too_early_expiration(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        UserSubscription.objects.create(
            user=User.objects.create(username="test", password="test"),
            subscription=Subscription.objects.create(
                name="AstroBin Premium",
                price=1,
                group=Group.objects.create(name="astrobin_premium")),
            expires=date(2021, 2, 19)
        )

        admin.submit_february_2020_data_loss_premium_upgrade(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_february_2020_data_loss_premium_upgrade_too_late_expiration(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        UserSubscription.objects.create(
            user=User.objects.create(username="test", password="test"),
            subscription=Subscription.objects.create(
                name="AstroBin Premium",
                price=1,
                group=Group.objects.create(name="astrobin_premium")),
            expires=date(2021, 2, 21)
        )

        admin.submit_february_2020_data_loss_premium_upgrade(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_february_2020_data_loss_premium_upgrade_sent(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        UserSubscription.objects.create(
            user=User.objects.create(username="test", password="test"),
            subscription=Subscription.objects.create(
                name="AstroBin Premium",
                price=1,
                group=Group.objects.create(name="astrobin_premium")),
            expires=date(2021, 2, 20)
        )

        admin.submit_february_2020_data_loss_premium_upgrade(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_called()
