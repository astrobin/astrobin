import datetime
import logging
from math import ceil
from typing import List, Optional

import stripe
from django.conf import settings
from django.contrib.auth.models import User
from stripe.error import StripeError
from subscription.models import Subscription, UserSubscription

from astrobin_apps_payments.models import ExchangeRate
from astrobin_apps_payments.types import StripeSubscription
from astrobin_apps_premium.services.premium_service import SubscriptionDisplayName, SubscriptionName

logger = logging.getLogger(__name__)


class PricingService:
    lite_2020: StripeSubscription = StripeSubscription(
        SubscriptionName.LITE_2020,
        SubscriptionDisplayName.LITE,
        settings.STRIPE['products']['non-recurring']['lite'],
        settings.STRIPE['prices']['non-recurring']['lite']['yearly'],
        None,
    )

    premium_2020: StripeSubscription = StripeSubscription(
        SubscriptionName.PREMIUM_2020,
        SubscriptionDisplayName.PREMIUM,
        settings.STRIPE['products']['non-recurring']['premium'],
        settings.STRIPE['prices']['non-recurring']['premium']['yearly'],
        None,
    )

    ultimate_2020: StripeSubscription = StripeSubscription(
        SubscriptionName.ULTIMATE_2020,
        SubscriptionDisplayName.ULTIMATE,
        settings.STRIPE['products']['non-recurring']['ultimate'],
        settings.STRIPE['prices']['non-recurring']['ultimate']['yearly'],
        None,
    )

    lite_2020_recurring: StripeSubscription = StripeSubscription(
        SubscriptionName.LITE_2020,
        SubscriptionDisplayName.LITE,
        settings.STRIPE['products']['recurring']['lite'],
        settings.STRIPE['prices']['recurring']['lite']['yearly'],
        settings.STRIPE['prices']['recurring']['lite']['monthly'],
    )

    premium_2020_recurring: StripeSubscription = StripeSubscription(
        SubscriptionName.PREMIUM_2020,
        SubscriptionDisplayName.PREMIUM,
        settings.STRIPE['products']['recurring']['premium'],
        settings.STRIPE['prices']['recurring']['premium']['yearly'],
        settings.STRIPE['prices']['recurring']['premium']['monthly'],
    )

    ultimate_2020_recurring: StripeSubscription = StripeSubscription(
        SubscriptionName.ULTIMATE_2020,
        SubscriptionDisplayName.ULTIMATE,
        settings.STRIPE['products']['recurring']['ultimate'],
        settings.STRIPE['prices']['recurring']['ultimate']['yearly'],
        settings.STRIPE['prices']['recurring']['ultimate']['monthly'],
    )

    @staticmethod
    def non_autorenewing_supported(user: Optional[User]) -> bool:
        if user is None or not user.is_authenticated:
            return False

        # Users who have had a non-autorenewing subscription less than 2 years ago can still opt to choose
        # non-autorenewal.
        return UserSubscription.objects.filter(
            user=user,
            subscription__recurrence_unit__isnull=True,
            expires__gt=datetime.date.today() - datetime.timedelta(days=365*2),
        ).exists()

    @staticmethod
    def get_available_subscriptions(user: User) -> List[StripeSubscription]:
        if PricingService.non_autorenewing_supported(user):
            return [
                PricingService.lite_2020_recurring,
                PricingService.premium_2020_recurring,
                PricingService.ultimate_2020_recurring,
                PricingService.lite_2020,
                PricingService.premium_2020,
                PricingService.ultimate_2020
            ]

        return [
            PricingService.lite_2020_recurring,
            PricingService.premium_2020_recurring,
            PricingService.ultimate_2020_recurring
        ]

    @staticmethod
    def get_price(product: str, currency: str, user: User = None) -> float:
        price = PricingService.get_full_price(product, currency)
        discount_amount = PricingService.get_discount_amount(product, currency, user)

        return price - discount_amount

    @staticmethod
    def get_full_price(product: str, currency: str) -> float:
        subscriptions = {
            'lite': Subscription.objects.get(name=SubscriptionName.LITE_2020.value),
            'premium': Subscription.objects.get(name=SubscriptionName.PREMIUM_2020.value),
            'ultimate': Subscription.objects.get(name=SubscriptionName.ULTIMATE_2020.value),
        }

        base_price = subscriptions[product].price
        # TODO
        return base_price
        # exchange_rate = ExchangeRate.objects.filter(
        #     target=currency.upper()).first().rate if currency.upper() != "CHF" else 1
        # exact_price = base_price * exchange_rate
        # rounded_price = ceil(exact_price * 2) / 2
        #
        # return rounded_price

    @staticmethod
    def get_discount_amount(product: str, currency: str, user: User = None) -> float:
        price = PricingService.get_full_price(product, currency)

        if user and user.is_authenticated:
            coupon = PricingService.get_stripe_coupon(user)
            customer = PricingService.get_stripe_customer(user)

            if coupon is None:
                return 0

            if customer is not None and not PricingService.is_new_customer(customer['id']):
                return 0

            if coupon['amount_off']:
                return coupon['amount_off']
            elif coupon['percent_off']:
                return price / 100 * coupon['percent_off']

        return 0

    @staticmethod
    def get_stripe_discounts(user: User):
        coupon = PricingService.get_stripe_coupon(user)
        customer = PricingService.get_stripe_customer(user)

        if coupon is None:
            return []

        if customer is not None and not PricingService.is_new_customer(customer['id']):
            return []

        return [{"coupon": coupon['id']}]

    @staticmethod
    def get_stripe_customer(user: User):
        stripe.api_key = settings.STRIPE['keys']['secret']
        customer = stripe.Customer.list(email=user.email, limit=1)
        if len(customer['data']) == 1:
            return customer['data'][0]

        return None

    @staticmethod
    def is_new_customer(customer_id: str) -> bool:
        stripe.api_key = settings.STRIPE['keys']['secret']
        charges = stripe.Charge.list(customer=customer_id, limit=1)

        if len(charges['data']) > 0:
            return False

        return True

    @staticmethod
    def get_stripe_coupon(user: User):
        referral_code = user.userprofile.referral_code

        if referral_code is None:
            return None

        try:
            stripe.api_key = settings.STRIPE['keys']['secret']
            coupon = stripe.Coupon.retrieve(referral_code)
            return coupon
        except StripeError as e:
            logger.warning("User %d tried to use non-existing coupon %s" % (user.pk, referral_code))
            return None
