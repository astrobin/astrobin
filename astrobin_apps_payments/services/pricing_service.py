import datetime
import logging
from typing import List, Optional

import stripe
from django.conf import settings
from django.contrib.auth.models import User
from stripe.error import StripeError
from subscription.models import UserSubscription

from astrobin_apps_payments.types import StripeSubscription
from astrobin_apps_payments.types.subscription_recurring_unit import SubscriptionRecurringUnit
from astrobin_apps_premium.services.premium_service import SubscriptionDisplayName, SubscriptionName

logger = logging.getLogger(__name__)


class PricingService:
    lite_2020: StripeSubscription = StripeSubscription(
        SubscriptionName.LITE_2020,
        SubscriptionDisplayName.LITE,
    )

    premium_2020: StripeSubscription = StripeSubscription(
        SubscriptionName.PREMIUM_2020,
        SubscriptionDisplayName.PREMIUM,
    )

    ultimate_2020: StripeSubscription = StripeSubscription(
        SubscriptionName.ULTIMATE_2020,
        SubscriptionDisplayName.ULTIMATE,
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
        return [
            PricingService.lite_2020,
            PricingService.premium_2020,
            PricingService.ultimate_2020
        ]

    @staticmethod
    def get_price(
            product_name: SubscriptionDisplayName,
            country_code: str,
            currency: str,
            recurring_unit: Optional[SubscriptionRecurringUnit] = None,
            user: Optional[User] = None
    ) -> float:
        full_price = PricingService.get_full_price(product_name, country_code, currency, recurring_unit)
        discount_amount = PricingService.get_discount_amount(product_name, country_code, currency, recurring_unit, user)
        prorate_amount = PricingService.get_prorate_amount(product_name, country_code, recurring_unit, user)

        price = full_price - discount_amount

        if prorate_amount > 0:
            price -= prorate_amount

        return price

    @staticmethod
    def get_full_price(
            product_name: SubscriptionDisplayName,
            country_code: str,
            currency: str,
            recurring_unit: Optional[SubscriptionRecurringUnit] = None
    ) -> float:
        return PricingService.get_stripe_price(
            product_name,
            country_code,
            currency,
            recurring_unit,
        )

    @staticmethod
    def get_prorate_amount(
            product_name: SubscriptionDisplayName,
            country_code: str,
            recurring_unit: SubscriptionRecurringUnit,
            user: Optional[User] = None
    ) -> float:
        # Set proration date to this moment:
        import time
        proration_date = int(time.time())

        if not user:
            return 0

        if not user.userprofile.stripe_subscription_id:
            return 0

        if not user.userprofile.stripe_customer_id:
            return 0

        # See what the next invoice would look like with a price switch
        # and proration set:
        stripe.api_key = settings.STRIPE['keys']['secret']
        subscription = stripe.Subscription.retrieve(user.userprofile.stripe_subscription_id)
        items = [{
            'id': subscription['items']['data'][0].id,
            'price': PricingService.get_stripe_price_object(product_name, country_code, recurring_unit)["id"]
        }]

        try:
            invoice = stripe.Invoice.upcoming(
                customer=user.userprofile.stripe_customer_id,
                subscription=user.userprofile.stripe_subscription_id,
                subscription_items=items,
                subscription_proration_date=proration_date,
            )
        except StripeError as e:
            return 0

        return -invoice['lines']['data'][0]['amount'] / 100

    @staticmethod
    def get_discount_amount(
            product_name: SubscriptionDisplayName,
            country_code: str,
            currency: str,
            recurring_unit: Optional[SubscriptionRecurringUnit] = None,
            user: User = None,
    ) -> float:
        price = PricingService.get_full_price(product_name, country_code, currency, recurring_unit)

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
        try:
            customer = stripe.Customer.list(email=user.email, limit=1)
            if len(customer['data']) == 1:
                return customer['data'][0]
        except StripeError as e:
            logger.error('Error retrieving Stripe customer %s: %s' % (user.email, e))

        return None

    @staticmethod
    def get_stripe_price_object(
            product_name: SubscriptionDisplayName,
            country_code: str,
            recurring_unit: Optional[SubscriptionRecurringUnit] = None
    ):
        # Tier 1: High-Income Countries
        tier_1 = [
            'AT',  # Austria
            'AU',  # Australia
            'BE',  # Belgium
            'CA',  # Canada
            'CH',  # Switzerland
            'DE',  # Germany
            'DK',  # Denmark
            'ES',  # Spain
            'FI',  # Finland
            'FR',  # France
            'GB',  # United Kingdom
            'IE',  # Ireland
            'IS',  # Iceland
            'JP',  # Japan
            'LU',  # Luxembourg
            'NL',  # Netherlands
            'NO',  # Norway
            'NZ',  # New Zealand
            'SE',  # Sweden
            'SG',  # Singapore
            'US'  # United States
        ]

        # Tier 2: Upper-Middle-Income Countries
        tier_2 = [
            'AR',  # Argentina
            'BR',  # Brazil
            'CL',  # Chile
            'CN',  # China
            'CR',  # Costa Rica
            'CZ',  # Czech Republic
            'EE',  # Estonia
            'GR',  # Greece
            'HU',  # Hungary
            'ID',  # Indonesia
            'IL',  # Israel
            'IN',  # India
            'IR',  # Iran
            'IT',  # Italy
            'KR',  # South Korea
            'LT',  # Lithuania
            'LV',  # Latvia
            'MT',  # Malta
            'MX',  # Mexico
            'MY',  # Malaysia
            'PA',  # Panama
            'PL',  # Poland
            'PT',  # Portugal
            'RU',  # Russia
            'SA',  # Saudi Arabia
            'SI',  # Slovenia
            'SK',  # Slovakia
            'TH',  # Thailand
            'TR',  # Turkey
            'UA',  # Ukraine
            'UY',  # Uruguay
            'ZA'  # South Africa
        ]

        # Tier 3: Lower-Middle-Income Countries
        tier_3 = [
            'AF',  # Afghanistan
            'BD',  # Bangladesh
            'CI',  # Ivory Coast
            'EG',  # Egypt
            'ET',  # Ethiopia
            'GH',  # Ghana
            'HT',  # Haiti
            'KE',  # Kenya
            'LB',  # Lebanon
            'LK',  # Sri Lanka
            'MA',  # Morocco
            'MM',  # Myanmar
            'MN',  # Mongolia
            'MZ',  # Mozambique
            'NG',  # Nigeria
            'PH',  # Philippines
            'PK',  # Pakistan
            'SD',  # Sudan
            'SN',  # Senegal
            'TZ',  # Tanzania
            'UG',  # Uganda
            'VN',  # Vietnam
            'YE',  # Yemen
            'ZM',  # Zambia
            'ZW'  # Zimbabwe
        ]

        recurring_unit_key = recurring_unit.value.lower() if recurring_unit is not None else 'one-year'

        if country_code.upper() in tier_1:
            recurring_unit_key += '-tier-1'
        elif country_code.upper() in tier_2:
            recurring_unit_key += '-tier-2'
        elif country_code.upper() in tier_3:
            recurring_unit_key += '-tier-3'
        else:
            recurring_unit_key += '-tier-1'
            logger.warning('Invalid country code %s, defaulting to tier 1' % country_code.upper())

        stripe.api_key = settings.STRIPE['keys']['secret']
        stripe_price_id = settings.STRIPE['prices'][product_name.value.lower()][recurring_unit_key]

        try:
            stripe_price = stripe.Price.retrieve(stripe_price_id, expand=['currency_options'])
            return stripe_price
        except StripeError as e:
            logger.error('Error retrieving Stripe price %s: %s' % (stripe_price_id, e))
            return None


    @staticmethod
    def get_stripe_price(
            product_name: SubscriptionDisplayName,
            country_code: str,
            currency: str,
            recurring_unit: Optional[SubscriptionRecurringUnit] = None
    ) -> float:
        stripe_price = PricingService.get_stripe_price_object(product_name, country_code, recurring_unit)
        if stripe_price:
            if currency.lower() not in stripe_price['currency_options']:
                currency = 'usd'
            return stripe_price['currency_options'][currency.lower()]['unit_amount'] / 100

        return 0


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
