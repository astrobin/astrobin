# Python
import datetime

# Django
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test import TestCase

# Third party
from subscription.models import Subscription, UserSubscription

# AstroBin
from astrobin.models import Image, UserProfile

# Premium
from astrobin_apps_premium.utils import *
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import *


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


    def test_subscription_validity(self):
        u = User.objects.create_user(
            username = 'test', email='test@test.com', password = 'password')
        g, created = Group.objects.get_or_create(name = "premium")
        s, created = Subscription.objects.get_or_create(
            name = "AstroBin Premium",
            price = 1,
            group = g,
            category = "premium")
        us, created = UserSubscription.objects.get_or_create(
            user = u,
            subscription = s)
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
        g, created = Group.objects.get_or_create(name = "lite")
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

    def test_upload_limits(self):
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

        Image.all_objects.filter(user = user).delete()
        profile = UserProfile.objects.get(pk = profile.pk)
        self.assertEqual(profile.premium_counter, 0)

        # Promote to Lite
        group, created = Group.objects.get_or_create(name = "premium")
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
        Image.all_objects.get(pk = 40).delete()
        profile = UserProfile.objects.get(pk = profile.pk)
        self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_FREE - 1)

        # But deleting an image uploaded before the subscription was created does not
        image = Image.all_objects.get(pk = 39)
        image.uploaded = image.uploaded - datetime.timedelta(days = 1)
        image.save()
        image.delete()
        profile = UserProfile.objects.get(pk = profile.pk)
        self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_FREE - 1)

        sub.delete()
        usersub.delete()

        # Promote to Premium
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
        counter = profile.premium_counter
        response = self.client.post(
            reverse('image_upload_process'),
            { 'image_file': open('astrobin/fixtures/test.jpg', 'rb') },
            follow = True)
        profile = UserProfile.objects.get(pk = profile.pk)
        self.assertEqual(profile.premium_counter, counter + 1)

        # But it never decreases, as it's not necessary
        image = Image.all_objects.all()[0]
        image.delete()
        profile = UserProfile.objects.get(pk = profile.pk)
        self.assertEqual(profile.premium_counter, counter + 1)

        user.delete()
        group.delete()
        sub.delete()
        usersub.delete()
