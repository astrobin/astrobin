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

    def test_test_notification_view(self):
        self.client.login(username='user1', password='password')
        response = self.client.post(
            reverse('astrobin_apps_notifications.test_notification',
                    args=('user2',)), {})
        self.assertEquals(response.status_code, 200)
        self.assertEquals("test_notification sent" in response.content, True)
        self.assertEquals(get_recent_notifications(self.user2).count(), 1)
        self.assertEquals(get_seen_notifications(self.user2).count(), 0)
        self.assertEquals(get_unseen_notifications(self.user2).count(), 1)
        self.client.logout()

    def test_notifications_table_tag(self):
        self.client.login(username='user1', password='password')
        response = self.client.post(
            reverse('astrobin_apps_notifications.test_notification',
                    args=('user2',)), {})
        self.client.logout()
        self.client.login(username='user2', password='password')

        response = notifications_table(self.user2, -1, -1)
        self.assertEquals(len(response['unseen']), 1)
        self.assertEquals(response['unseen'][0], get_unseen_notifications(self.user2)[0])
        self.assertEquals(len(response['seen']), 0)
        self.client.logout()
