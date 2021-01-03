import logging
from math import ceil

import stripe
from django.conf import settings
from django.contrib.auth.models import User
from stripe.error import StripeError
from subscription.models import Subscription

from astrobin_apps_payments.models import ExchangeRate

logger = logging.getLogger("apps")


class PricingService:
    @staticmethod
    def get_price(product, currency, user=None):
        # type: (unicode, unicode) -> float

        price = PricingService.get_full_price(product, currency)
        discount_amount = PricingService.get_discount_amount(product, currency, user)

        return price - discount_amount

    @staticmethod
    def get_full_price(product, currency):
        # type: (unicode, unicode) -> float

        subscriptions = {
            'lite': Subscription.objects.get(name='AstroBin Lite 2020+'),
            'premium': Subscription.objects.get(name='AstroBin Premium 2020+'),
            'ultimate': Subscription.objects.get(name='AstroBin Ultimate 2020+'),
        }

        base_price = subscriptions[product].price
        exchange_rate = ExchangeRate.objects.filter(
            target=currency.upper()).first().rate if currency.upper() != "CHF" else 1
        exact_price = base_price * exchange_rate
        rounded_price = ceil(exact_price * 2) / 2

        return rounded_price

    @staticmethod
    def get_discount_amount(product, currency, user=None, ):
        # type: (unicode, unicode) -> float

        price = PricingService.get_full_price(product, currency)

        if user and user.is_authenticated():
            coupon = PricingService._get_stripe_coupon(user)

            if coupon:
                if coupon['amount_off']:
                    return coupon['amount_off']
                elif coupon['percent_off']:
                    return price / 100 * coupon['percent_off']

        return 0

    @staticmethod
    def get_stripe_discounts(user):
        # type: (User) -> object

        coupon = PricingService._get_stripe_coupon(user)

        return [{"coupon": coupon['id']}]

    @staticmethod
    def _get_stripe_coupon(user):
        # type: (User) -> object

        referral_code = user.userprofile.referral_code

        if referral_code is None:
            return None

        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            coupon = stripe.Coupon.retrieve(referral_code)
            return coupon
        except StripeError as e:
            logger.warning("User %d tried to use non-existing coupon %s" % (user.pk, referral_code))
            return None
