# -*- coding: UTF-8

from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from mock import patch

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class ImageRetailerAffiliatesWhenOwnerIsPremiumAndDoesNotAllowTest(TestCase):
    def setUp(self):
        self.image = Generators.image()
        Generators.premium_subscription(self.image.user, "AstroBin Premium")

        self.image.user.userprofile.allow_retailer_integration = False
        self.image.user.userprofile.save()

        telescope = Generators.telescope()
        equipment_brand_listing = EquipmentGenerators.equipmentBrandListing()
        telescope.equipment_brand_listings.add(equipment_brand_listing)

        self.image.user.userprofile.telescopes.add(telescope)
        self.image.imaging_telescopes.add(telescope)

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_anon(self, retrieve_primary_thumbnails):
        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertContains(response, "retailer-affiliate-cart-link")

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_free(self, retrieve_primary_thumbnails):
        user = Generators.user()
        self.client.login(username=user.username, password="password")

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertContains(response, "retailer-affiliate-cart-link")

        user.userprofile.allow_retailer_integration = False
        user.userprofile.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertContains(response, "retailer-affiliate-cart-link")

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_lite_2020(self, retrieve_primary_thumbnails):
        user = Generators.user()
        self.client.login(username=user.username, password="password")
        Generators.premium_subscription(user, "AstroBin Lite 2020+")

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertContains(response, "retailer-affiliate-cart-link")

        user.userprofile.allow_retailer_integration = False
        user.userprofile.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertContains(response, "retailer-affiliate-cart-link")

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_lite(self, retrieve_primary_thumbnails):
        user = Generators.user()
        self.client.login(username=user.username, password="password")
        Generators.premium_subscription(user, "AstroBin Lite")

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertContains(response, "retailer-affiliate-cart-link")

        user.userprofile.allow_retailer_integration = False
        user.userprofile.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertNotContains(response, "retailer-affiliate-cart-link")

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_lite_autorenew(self, retrieve_primary_thumbnails):
        user = Generators.user()
        self.client.login(username=user.username, password="password")
        Generators.premium_subscription(user, "AstroBin Lite (autorenew)")

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertContains(response, "retailer-affiliate-cart-link")

        user.userprofile.allow_retailer_integration = False
        user.userprofile.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertNotContains(response, "retailer-affiliate-cart-link")

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_premium_2020(self, retrieve_primary_thumbnails):
        user = Generators.user()
        self.client.login(username=user.username, password="password")
        Generators.premium_subscription(user, "AstroBin Premium 2020+")

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertContains(response, "retailer-affiliate-cart-link")

        user.userprofile.allow_retailer_integration = False
        user.userprofile.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertNotContains(response, "retailer-affiliate-cart-link")

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_premium(self, retrieve_primary_thumbnails):
        user = Generators.user()
        self.client.login(username=user.username, password="password")
        Generators.premium_subscription(user, "AstroBin Premium")

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertContains(response, "retailer-affiliate-cart-link")

        user.userprofile.allow_retailer_integration = False
        user.userprofile.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertNotContains(response, "retailer-affiliate-cart-link")

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_premium_autorenew(self, retrieve_primary_thumbnails):
        user = Generators.user()
        self.client.login(username=user.username, password="password")
        Generators.premium_subscription(user, "AstroBin Premium (autorenew)")

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertContains(response, "retailer-affiliate-cart-link")

        user.userprofile.allow_retailer_integration = False
        user.userprofile.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertNotContains(response, "retailer-affiliate-cart-link")

    @override_settings(ADS_ENABLED=True)
    @patch("astrobin.tasks.retrieve_primary_thumbnails")
    def test_ultimate_2020(self, retrieve_primary_thumbnails):
        user = Generators.user()
        self.client.login(username=user.username, password="password")
        Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertNotContains(response, "retailer-affiliate-cart-link")

        user.userprofile.allow_retailer_integration = False
        user.userprofile.save()

        response = self.client.get(reverse('image_detail', kwargs={'id': self.image.get_id()}))
        self.assertNotContains(response, "dropdown retailer-affiliate-products-lite")
        self.assertNotContains(response, "retailer-affiliate-cart-link")
