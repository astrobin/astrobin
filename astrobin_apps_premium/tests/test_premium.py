from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch
from subscription.models import Subscription

from astrobin.models import Image, UserProfile
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import *
from astrobin_apps_premium.utils import *


class PremiumTest(TestCase):
    def _assertMessage(self, response, tags, content):
        messages = response.context[0]['messages']

        if len(messages) == 0:
            self.assertEqual(False, True)

        found = False
        for message in messages:
            if message.tags == tags and content in message.message:
                found = True

        self.assertEqual(found, True)


    def test_premium_get_usersubscription(self):
        with self.settings(PREMIUM_ENABLED = True):
            u = User.objects.create_user(username = 'test', email='test@test.com', password = 'password')
            g, created = Group.objects.get_or_create(name = "astrobin_premium")

            premium_sub, created = Subscription.objects.get_or_create(
                name = "AstroBin Premium",
                price = 1,
                group = g,
                category = "premium")

            premium_autorenew_sub, created = Subscription.objects.get_or_create(
                name = "AstroBin Premium (autorenew)",
                price = 1,
                group = g,
                category = "premium_autorenew")

            lite_sub, created = Subscription.objects.get_or_create(
                name = "AstroBin Lite",
                price = 1,
                group = g,
                category = "premium")

            lite_autorenew_sub, created = Subscription.objects.get_or_create(
                name = "AstroBin Lite (autorenew)",
                price = 1,
                group = g,
                category = "premium_autorenew")

            premium_us, created = UserSubscription.objects.get_or_create(user = u, subscription = premium_sub, cancelled = False)
            premium_us.subscribe()

            self.assertEqual(False, premium_us.cancelled)

            self.assertEqual(premium_us, premium_get_usersubscription(u))
            self.assertEqual(premium_us, premium_get_valid_usersubscription(u))

            premium_autorenew_us, created = UserSubscription.objects.get_or_create(user = u, subscription = premium_autorenew_sub, cancelled = False)
            premium_autorenew_us.subscribe()

            self.assertEqual(premium_us, premium_get_usersubscription(u))
            self.assertEqual(premium_us, premium_get_valid_usersubscription(u))

            lite_us, created = UserSubscription.objects.get_or_create(user = u, subscription = lite_sub, cancelled = False)
            lite_us.subscribe()

            self.assertEqual(premium_us, premium_get_usersubscription(u))
            self.assertEqual(premium_us, premium_get_valid_usersubscription(u))

            lite_autorenew_us, created = UserSubscription.objects.get_or_create(user = u, subscription = lite_autorenew_sub, cancelled = False)
            lite_autorenew_us.subscribe()

            self.assertEqual(premium_us, premium_get_usersubscription(u))
            self.assertEqual(premium_us, premium_get_valid_usersubscription(u))

            premium_us.active = False; premium_us.save()
            self.assertEqual(premium_autorenew_us, premium_get_valid_usersubscription(u))


    def test_subscription_validity(self):
        with self.settings(PREMIUM_ENABLED = True):
            u = User.objects.create_user(
                username = 'test', email='test@test.com', password = 'password')
            g, created = Group.objects.get_or_create(name = "astrobin_premium")
            s, created = Subscription.objects.get_or_create(
                name = "AstroBin Premium",
                price = 1,
                group = g,
                category = "premium")
            us, created = UserSubscription.objects.get_or_create(
                user = u,
                subscription = s,
                cancelled = False)
            us.subscribe()

            self.assertEqual(premium_get_usersubscription(u), us)
            self.assertEqual(premium_get_valid_usersubscription(u), us)
            self.assertEqual(premium_get_invalid_usersubscription(u), None)
            self.assertEqual(premium_user_has_subscription(u), True)
            self.assertEqual(premium_user_has_valid_subscription(u), True)
            self.assertEqual(premium_user_has_invalid_subscription(u), False)

            self.assertEqual(is_premium(u), True)

            us.unsubscribe()
            us.delete()
            s.delete()
            g.delete()
            u.delete()

            # Test Lite

            u = User.objects.create_user(
                username = 'test', email='test@test.com', password = 'password')
            g, created = Group.objects.get_or_create(name = "astrobin_lite")
            s, created = Subscription.objects.get_or_create(
                name = "AstroBin Lite",
                price = 1,
                group = g,
                category = "premium")
            us, created = UserSubscription.objects.get_or_create(
                user = u,
                subscription = s)
            us.subscribe()

            self.assertEqual(is_lite(u), True)

            # Test free
            us.unsubscribe()
            self.assertEqual(is_free(u), True)

            us.delete()
            s.delete()
            g.delete()
            u.delete()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_upload_limits(self, retrieve_primary_thumbnails):
        user = User.objects.create_user(
            username = 'test', email='test@test.com', password = 'password')
        profile = user.userprofile
        self.client.login(username = 'test', password = 'password')

        # Let's start with free
        self.assertEqual(user.userprofile.premium_counter, 0)
        for i in range(1, settings.PREMIUM_MAX_IMAGES_FREE + 1):
            response = self.client.post(
                reverse('image_upload_process'),
                { 'image_file': open('astrobin/fixtures/test.jpg', 'rb') },
                follow = True)
            profile = UserProfile.objects.get(pk = profile.pk)
            self.assertEqual(profile.premium_counter, i)

        response = self.client.post(
            reverse('image_upload_process'),
            { 'image_file': open('astrobin/fixtures/test.jpg', 'rb') },
            follow = True)
        self._assertMessage(response, "error unread", "You have reached your image count limit")

        # Promote to Lite
        group, created = Group.objects.get_or_create(name = "astrobin_lite")
        sub, created = Subscription.objects.get_or_create(
            name = "AstroBin Lite",
            price = 1,
            recurrence_unit = 'Y',
            recurrence_period = 1,
            group = group,
            category = "premium")
        usersub, created = UserSubscription.objects.get_or_create(
            user = user,
            subscription = sub)
        usersub.subscribe()
        usersub.extend()
        usersub.save()

        for i in range(1, settings.PREMIUM_MAX_IMAGES_FREE + 1):
            response = self.client.post(
                reverse('image_upload_process'),
                { 'image_file': open('astrobin/fixtures/test.jpg', 'rb') },
                follow = True)
            profile = UserProfile.objects.get(pk = profile.pk)
            self.assertEqual(profile.premium_counter, i)

        response = self.client.post(
            reverse('image_upload_process'),
            { 'image_file': open('astrobin/fixtures/test.jpg', 'rb') },
            follow = True)
        self._assertMessage(response, "error unread", "You have reached your image count limit")

        # Deleting an image uploaded this year decreases the counter as expected
        Image.objects_including_wip.all().last().delete()
        profile = UserProfile.objects.get(pk = profile.pk)
        self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_FREE - 1)

        # But deleting an image uploaded before the subscription was created does not
        image = Image.objects_including_wip.all().order_by('-pk')[1] # Second last element
        image.uploaded = image.uploaded - datetime.timedelta(days = 1)
        image.save(keep_deleted=True)
        image.delete()
        profile = UserProfile.objects.get(pk = profile.pk)
        self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_FREE - 1)

        sub.delete()
        usersub.delete()

        # Promote to Premium
        group, created = Group.objects.get_or_create(name = "astrobin_premium")
        sub, created = Subscription.objects.get_or_create(
            name = "AstroBin Premium",
            price = 1,
            group = group,
            category = "premium")
        usersub, created = UserSubscription.objects.get_or_create(
            user = user,
            subscription = sub)
        usersub.subscribe()

        # Counter increases for Premium users too
        profile = UserProfile.objects.get(pk = profile.pk)
        counter = profile.premium_counter
        response = self.client.post(
            reverse('image_upload_process'),
            { 'image_file': open('astrobin/fixtures/test.jpg', 'rb') },
            follow = True)
        profile = UserProfile.objects.get(pk = profile.pk)
        self.assertEqual(profile.premium_counter, counter + 1)

        # But it never decreases, as it's not necessary
        image = Image.objects_including_wip.all()[0]
        image.delete()
        profile = UserProfile.objects.get(pk = profile.pk)
        self.assertEqual(profile.premium_counter, counter + 1)

        user.delete()
        group.delete()
        sub.delete()
        usersub.delete()
