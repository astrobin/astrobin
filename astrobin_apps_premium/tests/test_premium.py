from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from mock import patch

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

    def setUp(self):
        self.user = User.objects.create_user(username='test', email='test@test.com', password='password')
        self.lite_group, created = Group.objects.get_or_create(name="astrobin_lite")
        self.premium_group, created = Group.objects.get_or_create(name="astrobin_premium")
        self.lite_2020_group, created = Group.objects.get_or_create(name="astrobin_lite_2020")
        self.premium_2020_group, created = Group.objects.get_or_create(name="astrobin_premium_2020")
        self.ultimate_2020_group, created = Group.objects.get_or_create(name="astrobin_ultimate_2020")

        self.ultimate_2020_sub, created = Subscription.objects.get_or_create(
            name="AstroBin Ultimate 2020+",
            price=1,
            group=self.ultimate_2020_group,
            category="premium")

        self.premium_2020_sub, created = Subscription.objects.get_or_create(
            name="AstroBin Premium 2020+",
            price=1,
            group=self.premium_2020_group,
            category="premium")

        self.lite_2020_sub, created = Subscription.objects.get_or_create(
            name="AstroBin Lite 2020+",
            price=1,
            group=self.lite_2020_group,
            category="premium")

        self.premium_sub, created = Subscription.objects.get_or_create(
            name="AstroBin Premium",
            price=1,
            group=self.premium_group,
            category="premium")

        self.premium_autorenew_sub, created = Subscription.objects.get_or_create(
            name="AstroBin Premium (autorenew)",
            price=1,
            group=self.premium_group,
            category="premium_autorenew")

        self.lite_sub, created = Subscription.objects.get_or_create(
            name="AstroBin Lite",
            price=1,
            group=self.lite_group,
            category="premium")

        self.lite_autorenew_sub, created = Subscription.objects.get_or_create(
            name="AstroBin Lite (autorenew)",
            price=1,
            group=self.lite_group,
            category="premium_autorenew")

    def tearDown(self):
        self.user.delete()

        self.lite_group.delete()
        self.premium_group.delete()
        self.lite_2020_group.delete()
        self.premium_2020_group.delete()
        self.ultimate_2020_group.delete()

        self.ultimate_2020_sub.delete()
        self.premium_sub.delete()
        self.premium_autorenew_sub.delete()
        self.lite_sub.delete()
        self.lite_autorenew_sub.delete()

    def test_premium_get_usersubscription_premium_priority(self):
        with self.settings(PREMIUM_ENABLED=True):
            premium_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.premium_sub, cancelled=False)
            premium_us.subscribe()

            self.assertEqual(False, premium_us.cancelled)

            self.assertEqual(premium_us, premium_get_usersubscription(self.user))
            self.assertEqual(premium_us, premium_get_valid_usersubscription(self.user))

            premium_autorenew_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.premium_autorenew_sub, cancelled=False)
            premium_autorenew_us.subscribe()

            self.assertEqual(premium_us, premium_get_usersubscription(self.user))
            self.assertEqual(premium_us, premium_get_valid_usersubscription(self.user))

            lite_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.lite_sub, cancelled=False)
            lite_us.subscribe()

            self.assertEqual(premium_us, premium_get_usersubscription(self.user))
            self.assertEqual(premium_us, premium_get_valid_usersubscription(self.user))

            lite_autorenew_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.lite_autorenew_sub, cancelled=False)
            lite_autorenew_us.subscribe()

            self.assertEqual(premium_us, premium_get_usersubscription(self.user))
            self.assertEqual(premium_us, premium_get_valid_usersubscription(self.user))

            premium_us.active = False
            premium_us.save()
            self.assertEqual(premium_autorenew_us, premium_get_valid_usersubscription(self.user))

    def test_premium_get_usersubscription_premium_2020_priority(self):
        with self.settings(PREMIUM_ENABLED=True):
            premium_2020_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.premium_2020_sub, cancelled=False)
            premium_2020_us.subscribe()

            self.assertEqual(premium_2020_us, premium_get_usersubscription(self.user))
            self.assertEqual(premium_2020_us, premium_get_valid_usersubscription(self.user))

            premium_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.premium_sub, cancelled=False)
            premium_us.subscribe()

            self.assertEqual(premium_2020_us, premium_get_usersubscription(self.user))
            self.assertEqual(premium_2020_us, premium_get_valid_usersubscription(self.user))

            premium_autorenew_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.premium_autorenew_sub, cancelled=False)
            premium_autorenew_us.subscribe()

            self.assertEqual(premium_2020_us, premium_get_usersubscription(self.user))
            self.assertEqual(premium_2020_us, premium_get_valid_usersubscription(self.user))

            lite_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.lite_sub, cancelled=False)
            lite_us.subscribe()

            self.assertEqual(premium_2020_us, premium_get_usersubscription(self.user))
            self.assertEqual(premium_2020_us, premium_get_valid_usersubscription(self.user))

            lite_autorenew_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.lite_autorenew_sub, cancelled=False)
            lite_autorenew_us.subscribe()

            self.assertEqual(premium_2020_us, premium_get_usersubscription(self.user))
            self.assertEqual(premium_2020_us, premium_get_valid_usersubscription(self.user))

            premium_2020_us.active = False
            premium_2020_us.save()
            self.assertEqual(premium_us, premium_get_valid_usersubscription(self.user))

    def test_premium_get_usersubscription_ultimate_2020_priority(self):
        with self.settings(PREMIUM_ENABLED=True):
            ultimate_2020_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.ultimate_2020_sub, cancelled=False)
            ultimate_2020_us.subscribe()

            self.assertEqual(ultimate_2020_us, premium_get_usersubscription(self.user))
            self.assertEqual(ultimate_2020_us, premium_get_valid_usersubscription(self.user))

            premium_2020_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.premium_2020_sub, cancelled=False)
            premium_2020_us.subscribe()

            self.assertEqual(ultimate_2020_us, premium_get_usersubscription(self.user))
            self.assertEqual(ultimate_2020_us, premium_get_valid_usersubscription(self.user))

            premium_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.premium_sub, cancelled=False)
            premium_us.subscribe()

            self.assertEqual(ultimate_2020_us, premium_get_usersubscription(self.user))
            self.assertEqual(ultimate_2020_us, premium_get_valid_usersubscription(self.user))

            premium_autorenew_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.premium_autorenew_sub, cancelled=False)
            premium_autorenew_us.subscribe()

            self.assertEqual(ultimate_2020_us, premium_get_usersubscription(self.user))
            self.assertEqual(ultimate_2020_us, premium_get_valid_usersubscription(self.user))

            lite_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.lite_sub, cancelled=False)
            lite_us.subscribe()

            self.assertEqual(ultimate_2020_us, premium_get_usersubscription(self.user))
            self.assertEqual(ultimate_2020_us, premium_get_valid_usersubscription(self.user))

            lite_autorenew_us, created = UserSubscription.objects.get_or_create(
                user=self.user, subscription=self.lite_autorenew_sub, cancelled=False)
            lite_autorenew_us.subscribe()

            self.assertEqual(ultimate_2020_us, premium_get_usersubscription(self.user))
            self.assertEqual(ultimate_2020_us, premium_get_valid_usersubscription(self.user))

            ultimate_2020_us.active = False
            ultimate_2020_us.save()
            self.assertEqual(premium_2020_us, premium_get_valid_usersubscription(self.user))

    def test_subscription_validity_lite(self):
        with self.settings(PREMIUM_ENABLED=True):
            us, created = UserSubscription.objects.get_or_create(
                user=self.user,
                subscription=self.lite_sub,
                cancelled=False)
            us.subscribe()

            self.assertEqual(premium_get_usersubscription(self.user), us)
            self.assertEqual(premium_get_valid_usersubscription(self.user), us)
            self.assertEqual(premium_get_invalid_usersubscription(self.user), None)
            self.assertEqual(premium_user_has_subscription(self.user), True)
            self.assertEqual(premium_user_has_valid_subscription(self.user), True)
            self.assertEqual(premium_user_has_invalid_subscription(self.user), False)

            self.assertEqual(is_lite(self.user), True)

            us.unsubscribe()
            us.delete()

    def test_subscription_validity_premium(self):
        with self.settings(PREMIUM_ENABLED=True):
            us, created = UserSubscription.objects.get_or_create(
                user=self.user,
                subscription=self.premium_sub,
                cancelled=False)
            us.subscribe()

            self.assertEqual(premium_get_usersubscription(self.user), us)
            self.assertEqual(premium_get_valid_usersubscription(self.user), us)
            self.assertEqual(premium_get_invalid_usersubscription(self.user), None)
            self.assertEqual(premium_user_has_subscription(self.user), True)
            self.assertEqual(premium_user_has_valid_subscription(self.user), True)
            self.assertEqual(premium_user_has_invalid_subscription(self.user), False)

            self.assertEqual(is_premium(self.user), True)

            us.unsubscribe()
            us.delete()

    def test_subscription_validity_lite_2020(self):
        with self.settings(PREMIUM_ENABLED=True):
            us, created = UserSubscription.objects.get_or_create(
                user=self.user,
                subscription=self.lite_2020_sub,
                cancelled=False)
            us.subscribe()

            self.assertEqual(premium_get_usersubscription(self.user), us)
            self.assertEqual(premium_get_valid_usersubscription(self.user), us)
            self.assertEqual(premium_get_invalid_usersubscription(self.user), None)
            self.assertEqual(premium_user_has_subscription(self.user), True)
            self.assertEqual(premium_user_has_valid_subscription(self.user), True)
            self.assertEqual(premium_user_has_invalid_subscription(self.user), False)

            self.assertEqual(is_lite(self.user), False)
            self.assertEqual(is_lite_2020(self.user), True)

            us.unsubscribe()
            us.delete()

    def test_subscription_validity_premium_2020(self):
        with self.settings(PREMIUM_ENABLED=True):
            us, created = UserSubscription.objects.get_or_create(
                user=self.user,
                subscription=self.premium_2020_sub,
                cancelled=False)
            us.subscribe()

            self.assertEqual(premium_get_usersubscription(self.user), us)
            self.assertEqual(premium_get_valid_usersubscription(self.user), us)
            self.assertEqual(premium_get_invalid_usersubscription(self.user), None)
            self.assertEqual(premium_user_has_subscription(self.user), True)
            self.assertEqual(premium_user_has_valid_subscription(self.user), True)
            self.assertEqual(premium_user_has_invalid_subscription(self.user), False)

            self.assertEqual(is_premium(self.user), False)
            self.assertEqual(is_premium_2020(self.user), True)

            us.unsubscribe()
            us.delete()

    def test_subscription_validity_ultimate_2020(self):
        with self.settings(PREMIUM_ENABLED=True):
            us, created = UserSubscription.objects.get_or_create(
                user=self.user,
                subscription=self.ultimate_2020_sub,
                cancelled=False)
            us.subscribe()

            self.assertEqual(premium_get_usersubscription(self.user), us)
            self.assertEqual(premium_get_valid_usersubscription(self.user), us)
            self.assertEqual(premium_get_invalid_usersubscription(self.user), None)
            self.assertEqual(premium_user_has_subscription(self.user), True)
            self.assertEqual(premium_user_has_valid_subscription(self.user), True)
            self.assertEqual(premium_user_has_invalid_subscription(self.user), False)

            self.assertEqual(is_ultimate_2020(self.user), True)

            us.unsubscribe()
            us.delete()

    @override_settings(PREMIUM_ENABLED=True)
    def test_subscription_validity_with_multiple(self):
        expired_ultimate, created = UserSubscription.objects.get_or_create(
            user=self.user,
            subscription=self.ultimate_2020_sub,
            cancelled=False)
        expired_ultimate.subscribe()
        expired_ultimate.expires = date.today() - timedelta(1)
        expired_ultimate.save()

        self.assertFalse(expired_ultimate.valid())

        premium, created = UserSubscription.objects.get_or_create(
            user=self.user,
            subscription=self.premium_2020_sub,
            cancelled=False)
        premium.subscribe()

        self.assertTrue(premium.valid())

        self.assertEqual(premium_get_valid_usersubscription(self.user), premium)
        self.assertEqual(premium_get_invalid_usersubscription(self.user), expired_ultimate)

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_upload_limits_free(self, retrieve_primary_thumbnails):
        """
        Free accounts can upload up to PREMIUM_MAX_IMAGES_FREE images.
        The counter does not decrease when deleting images.
        """
        self.client.login(username='test', password='password')

        with self.settings(PREMIUM_MAX_IMAGES_FREE=2):
            self.assertEqual(self.user.userprofile.premium_counter, 0)
            for i in [1, 2]:
                self.client.post(
                    reverse('image_upload_process'),
                    {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
                    follow=True)
                profile = UserProfile.objects.get(pk=self.user.userprofile.pk)
                self.assertEqual(profile.premium_counter, i)

            response = self.client.post(
                reverse('image_upload_process'),
                {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
                follow=True)
            self._assertMessage(response, "error unread", "You have reached your image count limit")

            # Deleting an image does not decrease the counter.
            Image.objects_including_wip.all().last().delete()
            profile = UserProfile.objects.get(pk=profile.pk)
            self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_FREE)

        Image.all_objects.filter(user=self.user).delete()
        self.user.userprofile.premium_counter = 0
        self.user.userprofile.save()

        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_upload_limits_lite(self, retrieve_primary_thumbnails):
        """
        Lite accounts (pre 2020, non-autorenew) can upload up to PREMIUM_MAX_IMAGES_LITE images per year.
        The counter decreases only when you delete an image uploaded during the current subscription period.
        """
        usersub, created = UserSubscription.objects.get_or_create(
            user=self.user,
            subscription=self.lite_sub,
            expires=datetime.datetime.now() + relativedelta(years=1))
        usersub.subscribe()

        self.client.login(username='test', password='password')

        with self.settings(PREMIUM_MAX_IMAGES_LITE=2):
            for i in [1, 2]:
                self.client.post(
                    reverse('image_upload_process'),
                    {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
                    follow=True)
                profile = UserProfile.objects.get(pk=self.user.userprofile.pk)
                self.assertEqual(profile.premium_counter, i)

            response = self.client.post(
                reverse('image_upload_process'),
                {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
                follow=True)
            self._assertMessage(response, "error unread", "You have reached your image count limit")

            # Deleting an image uploaded this year should decrease the counter.
            Image.objects_including_wip.all().last().delete()
            profile = UserProfile.objects.get(pk=profile.pk)
            self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_LITE - 1)
            Image.all_objects.last().undelete()

            # Deleting an image uploaded before the subscription was created does not decrease the counter.
            image = Image.objects_including_wip.all().order_by('-pk')[1]  # Second last element
            image.uploaded = image.uploaded - datetime.timedelta(days=2)
            image.save(keep_deleted=True)
            image.delete()
            profile = UserProfile.objects.get(pk=profile.pk)
            self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_LITE - 1)

        usersub.delete()

        Image.all_objects.filter(user=self.user).delete()
        self.user.userprofile.premium_counter = 0
        self.user.userprofile.save()

        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_upload_limits_premium(self, retrieve_primary_thumbnails):
        """
        Premium accounts (pre 2020, non-autorenew) can upload infinite images.
        The counter decreases, tho it's inconsequential.
        """
        usersub, created = UserSubscription.objects.get_or_create(
            user=self.user,
            subscription=self.premium_sub,
            expires=datetime.datetime.now() + relativedelta(years=1))
        usersub.subscribe()
        usersub.save()

        self.client.login(username='test', password='password')

        with self.settings(PREMIUM_MAX_IMAGES_PREMIUM=2):
            for i in [1, 2, 3]:
                self.client.post(
                    reverse('image_upload_process'),
                    {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
                    follow=True)
                profile = UserProfile.objects.get(pk=self.user.userprofile.pk)
                self.assertEqual(profile.premium_counter, i)

            # Deleting an image uploaded this year should decrease the counter.
            Image.objects_including_wip.all().last().delete()
            profile = UserProfile.objects.get(pk=profile.pk)
            self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_PREMIUM)

            # Deleting an image uploaded before the subscription was created does still decrease the counter.
            image = Image.objects_including_wip.all().order_by('-pk')[1]  # Second last element
            image.uploaded = image.uploaded - datetime.timedelta(days=1)
            image.save(keep_deleted=True)
            image.delete()
            profile = UserProfile.objects.get(pk=profile.pk)
            self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_PREMIUM - 1)

        usersub.delete()

        Image.all_objects.filter(user=self.user).delete()
        self.user.userprofile.premium_counter = 0
        self.user.userprofile.save()

        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_upload_limits_lite_autorenew(self, retrieve_primary_thumbnails):
        """
        Lite accounts (pre 2020, autorenew) can upload up to PREMIUM_MAX_IMAGES_LITE images per year.
        The counter decreases only when you delete an image uploaded during the current subscription period.
        """
        usersub, created = UserSubscription.objects.get_or_create(
            user=self.user,
            subscription=self.lite_autorenew_sub,
            expires=datetime.datetime.now() + relativedelta(years=1))
        usersub.subscribe()

        self.client.login(username='test', password='password')

        with self.settings(PREMIUM_MAX_IMAGES_LITE=2):
            for i in [1, 2]:
                self.client.post(
                    reverse('image_upload_process'),
                    {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
                    follow=True)
                profile = UserProfile.objects.get(pk=self.user.userprofile.pk)
                self.assertEqual(profile.premium_counter, i)

            response = self.client.post(
                reverse('image_upload_process'),
                {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
                follow=True)
            self._assertMessage(response, "error unread", "You have reached your image count limit")

            # Deleting an image uploaded this year should decrease the counter.
            Image.objects_including_wip.all().last().delete()
            profile = UserProfile.objects.get(pk=profile.pk)
            self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_LITE - 1)
            Image.all_objects.last().undelete()

            # Deleting an image uploaded before the subscription was created does not decrease the counter.
            image = Image.objects_including_wip.all().order_by('-pk')[1]  # Second last element
            image.uploaded = image.uploaded - datetime.timedelta(days=2)
            image.save(keep_deleted=True)
            image.delete()
            profile = UserProfile.objects.get(pk=profile.pk)
            self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_LITE - 1)

        usersub.delete()

        Image.all_objects.filter(user=self.user).delete()
        self.user.userprofile.premium_counter = 0
        self.user.userprofile.save()

        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_upload_limits_premium_autorenew(self, retrieve_primary_thumbnails):
        """
        Premium accounts (pre 2020, autorenew) can upload infinite images.
        The counter decreases, tho it's inconsequential.
        """
        usersub, created = UserSubscription.objects.get_or_create(
            user=self.user,
            subscription=self.premium_autorenew_sub,
            expires=datetime.datetime.now() + relativedelta(years=1))
        usersub.subscribe()
        usersub.save()

        self.client.login(username='test', password='password')

        with self.settings(PREMIUM_MAX_IMAGES_PREMIUM=2):
            for i in [1, 2, 3]:
                self.client.post(
                    reverse('image_upload_process'),
                    {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
                    follow=True)
                profile = UserProfile.objects.get(pk=self.user.userprofile.pk)
                self.assertEqual(profile.premium_counter, i)

            # Deleting an image uploaded this year should decrease the counter.
            Image.objects_including_wip.all().last().delete()
            profile = UserProfile.objects.get(pk=profile.pk)
            self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_PREMIUM)

            # Deleting an image uploaded before the subscription was created does still decrease the counter.
            image = Image.objects_including_wip.all().order_by('-pk')[1]  # Second last element
            image.uploaded = image.uploaded - datetime.timedelta(days=1)
            image.save(keep_deleted=True)
            image.delete()
            profile = UserProfile.objects.get(pk=profile.pk)
            self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_PREMIUM - 1)

        usersub.delete()

        Image.all_objects.filter(user=self.user).delete()
        self.user.userprofile.premium_counter = 0
        self.user.userprofile.save()

        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_upload_limits_lite_2020(self, retrieve_primary_thumbnails):
        """
        Lite 2020+ can upload up to PREMIUM_MAX_IMAGES_LITE_2020 images.
        The counter decreases on deletions.
        """
        usersub, created = UserSubscription.objects.get_or_create(
            user=self.user,
            subscription=self.lite_2020_sub,
            expires=datetime.datetime.now() + relativedelta(years=1))
        usersub.subscribe()

        self.client.login(username='test', password='password')

        with self.settings(PREMIUM_MAX_IMAGES_LITE_2020=2):
            for i in [1, 2]:
                self.client.post(
                    reverse('image_upload_process'),
                    {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
                    follow=True)
                profile = UserProfile.objects.get(pk=self.user.userprofile.pk)
                self.assertEqual(profile.premium_counter, i)

            response = self.client.post(
                reverse('image_upload_process'),
                {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
                follow=True)
            self._assertMessage(response, "error unread", "You have reached your image count limit")

            # Deleting an image uploaded this year should decrease the counter.
            Image.objects_including_wip.all().last().delete()
            profile = UserProfile.objects.get(pk=profile.pk)
            self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_LITE_2020 - 1)
            Image.all_objects.last().undelete()

            # Deleting an image uploaded before the subscription was created does decrease the counter.
            image = Image.objects_including_wip.all().order_by('-pk')[1]  # Second last element
            image.uploaded = image.uploaded - datetime.timedelta(days=1)
            image.save(keep_deleted=True)
            image.delete()
            profile = UserProfile.objects.get(pk=profile.pk)
            self.assertEqual(profile.premium_counter, settings.PREMIUM_MAX_IMAGES_LITE_2020 - 2)

        usersub.delete()

        Image.all_objects.filter(user=self.user).delete()
        self.user.userprofile.premium_counter = 0
        self.user.userprofile.save()

        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_upload_limits_premium_2020(self, retrieve_primary_thumbnails):
        """
        Premium 2020+ can upload unlimited images.
        The counter decreases.
        """
        usersub, created = UserSubscription.objects.get_or_create(
            user=self.user,
            subscription=self.premium_2020_sub,
            expires=datetime.datetime.now() + relativedelta(years=1))
        usersub.subscribe()

        self.client.login(username='test', password='password')

        for i in [1, 2]:
            self.client.post(
                reverse('image_upload_process'),
                {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
                follow=True)
            profile = UserProfile.objects.get(pk=self.user.userprofile.pk)
            self.assertEqual(profile.premium_counter, i)

        # Deleting an image uploaded this year should decrease the counter.
        Image.objects_including_wip.all().last().delete()
        profile = UserProfile.objects.get(pk=profile.pk)
        self.assertEqual(profile.premium_counter, 1)
        Image.all_objects.last().undelete()

        # Deleting an image uploaded before the subscription was created does still decrease the counter.
        image = Image.objects_including_wip.all().order_by('-pk')[1]  # Second last element
        image.uploaded = image.uploaded - datetime.timedelta(days=1)
        image.save(keep_deleted=True)
        image.delete()
        profile = UserProfile.objects.get(pk=profile.pk)
        self.assertEqual(profile.premium_counter, 0)

        usersub.delete()

        Image.all_objects.filter(user=self.user).delete()
        self.user.userprofile.premium_counter = 0
        self.user.userprofile.save()

        self.client.logout()

    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_upload_limits_ultimate_2020(self, retrieve_primary_thumbnails):
        """
        Ultimate 2020+ can upload infinite images.
        The counter decreases, even tho it's inconsequential.
        """
        usersub, created = UserSubscription.objects.get_or_create(
            user=self.user,
            subscription=self.ultimate_2020_sub,
            expires=datetime.datetime.now() + relativedelta(years=1))
        usersub.subscribe()

        self.client.login(username='test', password='password')

        with self.settings(ULTIMATE_MAX_IMAGES_PREMIUM_2020=2):
            # Upload one more than PREMIUM would allow.
            for i in [1, 2, 3]:
                self.client.post(
                    reverse('image_upload_process'),
                    {'image_file': open('astrobin/fixtures/test.jpg', 'rb')},
                    follow=True)
                profile = UserProfile.objects.get(pk=self.user.userprofile.pk)
                self.assertEqual(profile.premium_counter, i)

            # Deleting an image uploaded this year should decrease the counter.
            Image.objects_including_wip.all().last().delete()
            profile = UserProfile.objects.get(pk=profile.pk)
            self.assertEqual(profile.premium_counter, settings.ULTIMATE_MAX_IMAGES_PREMIUM_2020)
            Image.all_objects.last().undelete()

            # Deleting an image uploaded before the subscription was created does still decrease the counter.
            image = Image.objects_including_wip.all().order_by('-pk')[1]  # Second last element
            image.uploaded = image.uploaded - datetime.timedelta(days=1)
            image.save(keep_deleted=True)
            image.delete()
            profile = UserProfile.objects.get(pk=profile.pk)
            self.assertEqual(profile.premium_counter, settings.ULTIMATE_MAX_IMAGES_PREMIUM_2020 - 1)

        usersub.delete()

        Image.all_objects.filter(user=self.user).delete()
        self.user.userprofile.premium_counter = 0
        self.user.userprofile.save()

        self.client.logout()
