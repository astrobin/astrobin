# -*- coding: UTF-8

from django.test import TestCase, override_settings

from astrobin.models import UserProfile
from astrobin.tests.generators import Generators
from astrobin_apps_premium.services.premium_service import PremiumService


@override_settings(ADS_ENABLED=True)
class ImageRetailerAffiliatesWhenOwnerIsLiteAutorenewAndDoesNotAllowTest(TestCase):
    def setUp(self) -> None:
        owner = Generators.user()
        UserProfile.objects.filter(user=owner).update(allow_retailer_integration=False)
        owner.refresh_from_db()
        self.owner_us = Generators.premium_subscription(owner, SubscriptionName.LITE_CLASSIC_AUTORENEW)

    def test_anon_and_free(self):
        self.assertTrue(PremiumService.allow_full_retailer_integration(None, self.owner_us))

    def test_lite_2020(self):
        user = Generators.user()
        us = Generators.premium_subscription(user, SubscriptionName.LITE_2020)

        self.assertTrue(PremiumService.allow_full_retailer_integration(us, self.owner_us))

    def test_lite(self):
        user = Generators.user()
        us = Generators.premium_subscription(user, SubscriptionName.LITE_CLASSIC)

        self.assertTrue(PremiumService.allow_full_retailer_integration(us, self.owner_us))

    def test_lite_autorenew(self):
        user = Generators.user()
        us = Generators.premium_subscription(user, SubscriptionName.LITE_CLASSIC_AUTORENEW)

        self.assertTrue(PremiumService.allow_full_retailer_integration(us, self.owner_us))

    def test_premium_2020(self):
        user = Generators.user()
        us = Generators.premium_subscription(user, SubscriptionName.PREMIUM_2020)

        self.assertTrue(PremiumService.allow_full_retailer_integration(us, self.owner_us))

    def test_premium(self):
        user = Generators.user()
        us = Generators.premium_subscription(user, SubscriptionName.PREMIUM_CLASSIC)

        self.assertTrue(PremiumService.allow_full_retailer_integration(us, self.owner_us))

    def test_premium_autorenew(self):
        user = Generators.user()
        us = Generators.premium_subscription(user, SubscriptionName.PREMIUM_CLASSIC_AUTORENEW)

        self.assertTrue(PremiumService.allow_full_retailer_integration(us, self.owner_us))

    def test_ultimate_2020(self):
        user = Generators.user()
        us = Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)

        self.assertTrue(PremiumService.allow_full_retailer_integration(us, self.owner_us))

        UserProfile.objects.filter(user=user).update(allow_retailer_integration=False)
        us.refresh_from_db()

        self.assertFalse(PremiumService.allow_full_retailer_integration(us, self.owner_us))
