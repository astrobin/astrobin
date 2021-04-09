from datetime import datetime

from django.contrib.auth.models import Group
from django.test import TestCase
from subscription.models import Subscription

from astrobin_apps_payments.models import ExchangeRate
from astrobin_apps_payments.services.pricing_service import PricingService


class PricingServiceTest(TestCase):
    def setUp(self):
        Subscription.objects.create(
            name="AstroBin Lite 2020+",
            price=20,
            group=Group.objects.create(name='astrobin_lite')
        )

        Subscription.objects.create(
            name="AstroBin Premium 2020+",
            price=40,
            group=Group.objects.create(name='astrobin_premium')
        )

        Subscription.objects.create(
            name="AstroBin Ultimate 2020+",
            price=60,
            group=Group.objects.create(name='astrobin_ultimate')
        )

        ExchangeRate.objects.create(
            source='CHF',
            target='USD',
            rate=1.1,
            time=datetime.now()
        )

        ExchangeRate.objects.create(
            source='CHF',
            target='EUR',
            rate=1.101,
            time=datetime.now()
        )

    def test_chf(self):
        self.assertEquals(20, PricingService.get_price('lite', 'CHF'))
        self.assertEquals(40, PricingService.get_price('premium', 'CHF'))
        self.assertEquals(60, PricingService.get_price('ultimate', 'CHF'))


    def test_usd(self):
        self.assertEquals(22.0, PricingService.get_price('lite', 'USD'))
        self.assertEquals(44.0, PricingService.get_price('premium', 'USD'))
        self.assertEquals(66.0, PricingService.get_price('ultimate', 'USD'))

    def test_eur_with_50c_rounding_up(self):
        self.assertEquals(22.5, PricingService.get_price('lite', 'EUR'))
        self.assertEquals(44.5, PricingService.get_price('premium', 'EUR'))
        self.assertEquals(66.5, PricingService.get_price('ultimate', 'EUR'))
