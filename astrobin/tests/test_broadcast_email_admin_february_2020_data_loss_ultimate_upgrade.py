from datetime import date

from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from django.test import TestCase, RequestFactory
from mock import patch
from subscription.models import UserSubscription, Subscription

from astrobin.admin import BroadcastEmailAdmin
from astrobin.models import BroadcastEmail


class BroadcastEmailAdminFebruary2020DataLossUltimateUpgradeTest(TestCase):
    @patch("astrobin.tasks.send_broadcast_email.delay")
    def test_submit_february_2020_data_loss_ultimate_upgrade_no_users(self, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        admin.submit_february_2020_data_loss_ultimate_upgrade(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_february_2020_data_loss_ultimate_upgrade_no_premium(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        User.objects.create(username="test", password="test")

        admin.submit_february_2020_data_loss_ultimate_upgrade(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_february_2020_data_loss_premium_ultimate_too_early_expiration(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        UserSubscription.objects.create(
            user=User.objects.create(username="test", password="test"),
            subscription=Subscription.objects.create(
                name="AstroBin Premium",
                price=1,
                group=Group.objects.create(name="astrobin_premium")),
            expires=date(2020, 2, 14)
        )

        admin.submit_february_2020_data_loss_ultimate_upgrade(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_february_2020_data_loss_ultimate_upgrade_came_from_free_or_lite(self, messageUserMock, taskMock):
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

        admin.submit_february_2020_data_loss_ultimate_upgrade(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_february_2020_data_loss_ultimate_already_got_ultimate(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())
        user = User.objects.create(username="test", password="test")

        premium = UserSubscription.objects.create(
            user=user,
            subscription=Subscription.objects.create(
                name="AstroBin Premium",
                price=1,
                group=Group.objects.create(name="astrobin_premium")),
            expires=date(2020, 2, 20)
        )

        premium.subscribe()

        ultimate = UserSubscription.objects.create(
            user=user,
            subscription=Subscription.objects.create(
                name="AstroBin Ultimate 2020+",
                price=1,
                group=Group.objects.create(name="astrobin_ultimate_2020")),
            expires=date(2021, 3, 28)
        )

        ultimate.subscribe()

        admin.submit_february_2020_data_loss_ultimate_upgrade(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_february_2020_data_loss_ultimate_upgrade_sent(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        UserSubscription.objects.create(
            user=User.objects.create(username="test", password="test"),
            subscription=Subscription.objects.create(
                name="AstroBin Premium",
                price=1,
                group=Group.objects.create(name="astrobin_premium")),
            expires=date(2020, 2, 20)
        )

        admin.submit_february_2020_data_loss_ultimate_upgrade(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_called()
