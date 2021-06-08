from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from astrobin_apps_notifications.templatetags.astrobin_apps_notifications_tags import *
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
        url_parse = urlparse.urlparse(url)
        query = url_parse.query
        self.assertTrue('utm_source=astrobin' in query)
        self.assertTrue('utm_medium=email' in query)
        self.assertTrue('utm_campaign=notification' in query)

    def test_build_notification_url_with_other_params(self):
        url = build_notification_url('www.astrobin.com?foo=bar')
        url_parse = urlparse.urlparse(url)
        query = url_parse.query
        self.assertTrue('utm_source=astrobin' in query)
        self.assertTrue('utm_medium=email' in query)
        self.assertTrue('utm_campaign=notification' in query)
        self.assertTrue('foo=bar' in query)
