from datetime import datetime

from django.contrib.admin import AdminSite
from django.test import TestCase, RequestFactory
from mock import patch

from astrobin.admin import BroadcastEmailAdmin
from astrobin.models import BroadcastEmail
from astrobin.tests.generators import Generators


class BroadcastEmailAdminRecoveredImagesNoticeFrTest(TestCase):
    @patch("astrobin.tasks.send_broadcast_email.delay")
    def test_submit_recovered_images_notice_fr_no_users(self, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())

        admin.submit_recovered_images_notice_fr(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    def test_submit_recovered_images_notice_fr_no_recovered_images(self, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())
        user = Generators.user()
        Generators.image(user=user)

        admin.submit_recovered_images_notice_fr(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    def test_submit_recovered_images_notice_fr_wrong_language(self, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())
        user = Generators.user()
        user.userprofile.language = 'en'
        user.userprofile.save(keep_deleted=True)
        Generators.image(user=user, recovered=datetime.now())

        admin.submit_recovered_images_notice_fr(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    def test_submit_recovered_images_notice_fr_already_sent(self, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())
        user = Generators.user()
        user.userprofile.recovered_images_notice_sent = datetime.now()
        user.userprofile.save(keep_deleted=True)
        Generators.image(user=user, recovered=datetime.now())

        admin.submit_recovered_images_notice_fr(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_not_called()

    @patch("astrobin.tasks.send_broadcast_email.delay")
    @patch("django.contrib.admin.ModelAdmin.message_user")
    def test_submit_recovered_images_notice_fr_sent(self, messageUserMock, taskMock):
        request = RequestFactory().get("/")

        email = BroadcastEmail.objects.create(subject="test")
        admin = BroadcastEmailAdmin(model=BroadcastEmail, admin_site=AdminSite())
        user = Generators.user()
        user.userprofile.language = 'fr'
        user.userprofile.save(keep_deleted=True)
        Generators.image(user=user, recovered=datetime.now())

        admin.submit_recovered_images_notice_fr(request, BroadcastEmail.objects.filter(pk=email.pk))

        taskMock.assert_called()
        user.userprofile.refresh_from_db()
        self.assertIsNotNone(user.userprofile.recovered_images_notice_sent)
