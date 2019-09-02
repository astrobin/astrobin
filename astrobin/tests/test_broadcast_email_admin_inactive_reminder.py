from datetime import timedelta

from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.utils import timezone
from mock import patch

from astrobin.admin import BroadcastEmailAdmin, Image
from astrobin.models import BroadcastEmail


class BroadcastEmailAdminInactiveReminderTest(TestCase):
    @patch("astrobin.tasks.send_broadcast_email.delay")
    def test_submit_inactive_account_reminder_no_users(self, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        admin.submit_inactive_email_reminder(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_inactive_account_reminder_no_images(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        User.objects.create(username="inactive", password="inactive")

        admin.submit_inactive_email_reminder(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_inactive_account_reminder_too_recent_image(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="inactive", password="inactive")
        Image.objects.create(user=user)

        admin.submit_inactive_email_reminder(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_inactive_account_reminder_already_sent(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="inactive", password="inactive")
        user.userprofile.inactive_account_reminder_sent = timezone.now() - timedelta(days=7)
        user.userprofile.save()
        image = Image.objects.create(user=user)
        image.uploaded = image.uploaded - timedelta(61)
        image.save()

        admin.submit_inactive_email_reminder(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_inactive_account_reminder_already_sent_but_long_ago(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="inactive", password="inactive", email="email@email.com")
        user.userprofile.inactive_account_reminder_sent = timezone.now() - timedelta(days=90)
        user.userprofile.save()
        image = Image.objects.create(user=user)
        image.uploaded = image.uploaded - timedelta(61)
        image.save()

        admin.submit_inactive_email_reminder(request, BroadcastEmail.objects.filter(pk=email.pk))

        args, kwargs = taskMock.call_args
        taskMock.assert_called()
        self.assertEquals(["email@email.com"], list(args[1]))

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_inactive_account_reminder_success(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        user = User.objects.create(username="inactive", password="inactive", email="email@email.com")
        image = Image.objects.create(user=user)
        image.uploaded = image.uploaded - timedelta(61)
        image.save()

        admin.submit_inactive_email_reminder(request, BroadcastEmail.objects.filter(pk=email.pk))

        args, kwargs = taskMock.call_args
        taskMock.assert_called()
        self.assertEquals(["email@email.com"], list(args[1]))
