from datetime import timedelta

from django.test import TestCase

from astrobin.tests.generators import Generators
from astrobin_apps_premium.services.premium_service import PremiumService, SubscriptionName
from common.services import DateTimeService


class PremiumServiceTest(TestCase):
    def test_compare_validity(self):
        user = Generators.user()
        ultimate = Generators.premium_subscription(user, SubscriptionName.ULTIMATE_2020)
        lite = Generators.premium_subscription(user, SubscriptionName.LITE_2020)

        ultimate.expires = DateTimeService.today() + timedelta(60)
        ultimate.active = True
        ultimate.save()

        lite.expires = DateTimeService.today() + timedelta(30)
        lite.active = True
        lite.save()

        self.assertTrue(ultimate.valid())
        self.assertTrue(lite.valid())
        self.assertEqual(ultimate, PremiumService(user).get_valid_usersubscription())
