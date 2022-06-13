from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from astrobin_apps_notifications.utils import *


class NotificationsTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@test.com",
            password="password")
        self.user2 = User.objects.create_user(
            username="user2",
            email="user1@test.com",
            password="password")

    def tearDown(self):
        self.user1.delete()
        self.user2.delete()

    def test_build_notification_url_no_other_params(self):
        url = build_notification_url('www.astrobin.com')
        parsed = urlparse(url)
        query = parsed.query
        self.assertTrue('utm_source=astrobin' in query)
        self.assertTrue('utm_medium=email' in query)
        self.assertTrue('utm_campaign=notification' in query)

    def test_build_notification_url_with_other_params(self):
        url = build_notification_url('www.astrobin.com?foo=bar')
        parsed = urlparse(url)
        query = parsed.query
        self.assertTrue('utm_source=astrobin' in query)
        self.assertTrue('utm_medium=email' in query)
        self.assertTrue('utm_campaign=notification' in query)
        self.assertTrue('foo=bar' in query)

    @override_settings(
        BASE_URL="https://www.astrobin.com",
        APP_URL="https://app.astrobin.com"
    )
    def test_build_notification_url_base_url_and_app_url(self):
        url = build_notification_url(f'{settings.BASE_URL}{settings.APP_URL}/foo')
        self.assertFalse(settings.BASE_URL in url)
        self.assertTrue(settings.APP_URL in url)
