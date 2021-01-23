# -*- coding: UTF-8

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from mock import patch

from astrobin.tests.generators import Generators


class ImageAdsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'test', 'test@test.com', 'password')

    @override_settings(ADS_ENABLED=True)

    def test_image_anon_see_ads(self):
        image = Generators.image()
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "subtle-container advertisement")

    @override_settings(ADS_ENABLED=True)

    def test_image_free_see_ads(self):
        image = Generators.image()
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "subtle-container advertisement")

    @override_settings(ADS_ENABLED=True)

    def test_image_free_see_ads_with_allow_ads_as_false(self):
        image = Generators.image()
        self.user.userprofile.allow_astronomy_ads = False
        self.user.userprofile.save()
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "subtle-container advertisement")

    @override_settings(ADS_ENABLED=True)

    def test_image_lite_see_ads(self):
        image = Generators.image()
        Generators.premium_subscription(self.user, "AstroBin Lite")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "subtle-container advertisement")

    @override_settings(ADS_ENABLED=True)

    def test_image_lite_dont_see_ads_with_allow_ads_as_false(self):
        image = Generators.image()
        Generators.premium_subscription(self.user, "AstroBin Lite")
        self.user.userprofile.allow_astronomy_ads = False
        self.user.userprofile.save()
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertNotContains(response, "subtle-container advertisement")

    @override_settings(ADS_ENABLED=True)

    def test_image_lite_2020_see_ads(self):
        image = Generators.image()
        Generators.premium_subscription(self.user, "AstroBin Lite 2020+")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "subtle-container advertisement")

    @override_settings(ADS_ENABLED=True)

    def test_image_lite_2020_see_ads_with_allow_ads_as_false(self):
        image = Generators.image()
        Generators.premium_subscription(self.user, "AstroBin Lite 2020+")
        self.user.userprofile.allow_astronomy_ads = False
        self.user.userprofile.save()
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "subtle-container advertisement")

    @override_settings(ADS_ENABLED=True)

    def test_image_premium_see_ads(self):
        image = Generators.image()
        Generators.premium_subscription(self.user, "AstroBin Premium")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "subtle-container advertisement")

    @override_settings(ADS_ENABLED=True)

    def test_image_premium_dont_see_ads_with_allow_ads_as_false(self):
        image = Generators.image()
        Generators.premium_subscription(self.user, "AstroBin Premium")
        self.user.userprofile.allow_astronomy_ads = False
        self.user.userprofile.save()
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertNotContains(response, "subtle-container advertisement")

    @override_settings(ADS_ENABLED=True)

    def test_image_premium_2020_see_ads(self):
        image = Generators.image()
        Generators.premium_subscription(self.user, "AstroBin Premium 2020+")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "subtle-container advertisement")

    @override_settings(ADS_ENABLED=True)

    def test_image_premium_2020_dont_see_ads_with_allow_ads_as_false(self):
        image = Generators.image()
        Generators.premium_subscription(self.user, "AstroBin Premium 2020+")
        self.user.userprofile.allow_astronomy_ads = False
        self.user.userprofile.save()
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertNotContains(response, "subtle-container advertisement")

    @override_settings(ADS_ENABLED=True)

    def test_image_ultimate_2020_see_ads(self):
        image = Generators.image()
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertContains(response, "subtle-container advertisement")

    @override_settings(ADS_ENABLED=True)

    def test_image_ultimate_2020_dont_see_ads_with_allow_ads_as_false(self):
        image = Generators.image()
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        self.user.userprofile.allow_astronomy_ads = False
        self.user.userprofile.save()
        self.client.login(username='test', password='password')
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertNotContains(response, "subtle-container advertisement")

    @override_settings(ADS_ENABLED=True)

    def test_image_free_users_dont_see_ads_on_ultimate_2020_images(self):
        image = Generators.image()
        image.user = self.user
        image.save()
        Generators.premium_subscription(self.user, "AstroBin Ultimate 2020+")
        response = self.client.get(reverse('image_detail', kwargs={'id': image.get_id()}))
        self.assertNotContains(response, "subtle-container advertisement")
