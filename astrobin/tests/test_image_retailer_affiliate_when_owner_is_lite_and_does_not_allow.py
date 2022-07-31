# -*- coding: UTF-8

from django.urls import reverse
from django.test import TestCase, override_settings
from mock import patch

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators

# -*- coding: UTF-8

from django.test import TestCase, override_settings

from astrobin.models import UserProfile
from astrobin.tests.generators import Generators
from astrobin_apps_premium.services.premium_service import PremiumService


@override_settings(ADS_ENABLED=True)
class ImageRetailerAffiliatesWhenOwnerIsLiteAndDoesNotAllowTest(TestCase):
    def setUp(self) -> None:
        owner = Generators.user()
        UserProfile.objects.filter(user=owner).update(allow_retailer_integration=False)
        owner.refresh_from_db()
        self.owner_us = Generators.premium_subscription(owner, "AstroBin Lite")

    def test_anon_and_free(self):
        self.assertTrue(PremiumService.allow_full_retailer_integration(None, self.owner_us))

    def test_lite_2020(self):
        user = Generators.user()
        us = Generators.premium_subscription(user, "AstroBin Lite 2020+")

        self.assertTrue(PremiumService.allow_full_retailer_integration(us, self.owner_us))

    def test_lite(self):
        user = Generators.user()
        us = Generators.premium_subscription(user, "AstroBin Lite")

        self.assertTrue(PremiumService.allow_full_retailer_integration(us, self.owner_us))

    def test_lite_autorenew(self):
        user = Generators.user()
        us = Generators.premium_subscription(user, "AstroBin Lite (autorenew)")

        self.assertTrue(PremiumService.allow_full_retailer_integration(us, self.owner_us))

    def test_premium_2020(self):
        user = Generators.user()
        us = Generators.premium_subscription(user, "AstroBin Premium 2020+")

        self.assertTrue(PremiumService.allow_full_retailer_integration(us, self.owner_us))

    def test_premium(self):
        user = Generators.user()
        us = Generators.premium_subscription(user, "AstroBin Premium")

        self.assertTrue(PremiumService.allow_full_retailer_integration(us, self.owner_us))

    def test_premium_autorenew(self):
        user = Generators.user()
        us = Generators.premium_subscription(user, "AstroBin Premium (autorenew)")

        self.assertTrue(PremiumService.allow_full_retailer_integration(us, self.owner_us))

    def test_ultimate_2020(self):
        user = Generators.user()
        us = Generators.premium_subscription(user, "AstroBin Ultimate 2020+")

        self.assertTrue(PremiumService.allow_full_retailer_integration(us, self.owner_us))

        UserProfile.objects.filter(user=user).update(allow_retailer_integration=False)
        us.refresh_from_db()

        self.assertFalse(PremiumService.allow_full_retailer_integration(us, self.owner_us))
