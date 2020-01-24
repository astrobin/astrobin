from datetime import datetime

import persistent_messages
from django.contrib.auth.models import User, Group
from django.test import TestCase
from persistent_messages.models import Message
from subscription.models import Subscription, UserSubscription
from toggleproperties.models import ToggleProperty

from astrobin.models import App, Image


class APITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'test', 'test@test.com', 'password'
        )

        self.user2 = User.objects.create_user(
            'test2', 'test2@test.com', 'password'
        )

        self.app = App.objects.create(
            registrar=self.user,
            name="Test",
            description="Test",
            key="test-key",
            secret="test-secret",
        )

    def tearDown(self):
        self.app.delete()
        self.user.delete()

    def _get(self):
        return self.client.get("/api/v1/userprofile/%d/?api_key=%s&api_secret=%s&format=json" % (
            self.user.userprofile.pk,
            self.app.key,
            self.app.secret
        ))

    def test_api_userprofile_username(self):
        self.assertContains(self._get(), "\"username\": \"%s\"" % self.user.username)

    def test_api_userprofile_last_login(self):
        now = datetime.now()
        self.user.last_login = now
        self.user.save()

        self.assertContains(self._get(), "\"last_login\": \"%s\"" % now.isoformat())

    def test_api_userprofile_date_jooined(self):
        self.assertContains(self._get(), "\"date_joined\": \"%s\"" % self.user.date_joined.isoformat())

    def test_api_userprofile_image_count(self):
        self.assertContains(self._get(), "\"image_count\": 0")

        image = Image.objects.create(
            user=self.user
        )

        self.assertContains(self._get(), "\"image_count\": 1")

        image.delete()

    def test_api_userprofile_received_likes_count(self):
        self.assertContains(self._get(), "\"received_likes_count\": 0")

        image = Image.objects.create(
            user=self.user
        )

        like = ToggleProperty.objects.create(
            property_type='like',
            user=self.user2,
            content_object=image

        )

        self.assertContains(self._get(), "\"received_likes_count\": 1")

        like.delete()
        image.delete()


    def test_api_userprofile_followers_count(self):
        self.assertContains(self._get(), "\"followers_count\": 0")

        follow = ToggleProperty.objects.create(
            property_type='follow',
            user=self.user2,
            content_object=self.user

        )

        self.assertContains(self._get(), "\"followers_count\": 1")

        follow.delete()

    def test_api_userprofile_following_count(self):
        self.assertContains(self._get(), "\"following_count\": 0")

        follow = ToggleProperty.objects.create(
            property_type='follow',
            user=self.user,
            content_object=self.user2

        )

        self.assertContains(self._get(), "\"following_count\": 1")

        follow.delete()

    def test_api_userprofile_notifications_count(self):
        self.assertContains(self._get(), "\"total_notifications_count\": 0")
        self.assertContains(self._get(), "\"unread_notifications_count\": 0")

        notification = Message.objects.create(
            user=self.user,
            from_user=self.user,
            subject="Test notification",
            message="Test body",
            level=persistent_messages.INFO,

        )

        self.assertContains(self._get(), "\"total_notifications_count\": 1")
        self.assertContains(self._get(), "\"unread_notifications_count\": 1")

        notification.read = True
        notification.save()

        self.assertContains(self._get(), "\"total_notifications_count\": 1")
        self.assertContains(self._get(), "\"unread_notifications_count\": 0")

        notification.delete()

    def test_api_userprofilee_premium_subscription(self):
        self.assertContains(self._get(), "\"premium_subscription\": null")
        self.assertContains(self._get(), "\"premium_subscription_expiration\": null")

        group, created = Group.objects.get_or_create(name="astrobin_premium")

        premium_sub, created = Subscription.objects.get_or_create(
            name="AstroBin Premium",
            price=1,
            group=group,
            category="premium")

        premium_us, created = UserSubscription.objects.get_or_create(
            user=self.user,
            subscription=premium_sub,
            cancelled=False)

        premium_us.subscribe()

        self.assertContains(self._get(), "\"premium_subscription\": \"AstroBin Premium\"")
        self.assertContains(self._get(), "\"premium_subscription_expiration\": \"%s\"" % premium_us.expires.isoformat())

        premium_us.delete()
        premium_sub.delete()
        group.delete()
