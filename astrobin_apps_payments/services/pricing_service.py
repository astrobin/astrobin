import datetime
import logging
from typing import List, Optional

import stripe
from django.conf import settings
from django.contrib.auth.models import User
from stripe.error import StripeError
from subscription.models import UserSubscription

from astrobin.utils import get_client_country_code
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

        # User who have had an autorecurring Stripe subscription in the past cannot switch back.
        if (UserSubscription.objects.filter(
            user=user,
            subscription__name__in=[
                SubscriptionName.LITE_2020_AUTORENEW_MONTHLY.value,
                SubscriptionName.LITE_2020_AUTORENEW_YEARLY.value,
                SubscriptionName.PREMIUM_2020_AUTORENEW_MONTHLY.value,
                SubscriptionName.PREMIUM_2020_AUTORENEW_YEARLY.value,
                SubscriptionName.ULTIMATE_2020_AUTORENEW_MONTHLY.value,
                SubscriptionName.ULTIMATE_2020_AUTORENEW_YEARLY.value,
            ]
        )).exists():
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

        if not user.is_authenticated:
            return 0

        if not user.userprofile.stripe_subscription_id:
            return 0

        if not user.userprofile.stripe_customer_id:
            return 0

        # See what the next invoice would look like with a price switch
        # and proration set:
        stripe.api_key = settings.STRIPE['keys']['secret']
        subscription = stripe.Subscription.retrieve(user.userprofile.stripe_subscription_id)

        if not subscription or subscription['status'] != 'active':
            return 0

        items = [{
            'id': subscription['items']['data'][0].id,
            'price': PricingService.get_stripe_price_object(product_name, country_code, recurring_unit)["id"]
        }]

        customer = PricingService.get_stripe_customer(user)

        if not customer:
            logger.error('Error retrieving Stripe customer %s' % user.userprofile.stripe_customer_id)
            return 0

        try:
            invoice = stripe.Invoice.upcoming(
                customer=customer.id,
                subscription=user.userprofile.stripe_subscription_id,
                subscription_items=items,
                subscription_proration_date=proration_date,
            )
        except StripeError as e:
            logger.error(e)
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

        if user.userprofile.stripe_customer_id:
            try:
                customer = stripe.Customer.retrieve(user.userprofile.stripe_customer_id)
                if hasattr(customer, 'deleted') and customer.deleted:
                    raise StripeError
                return customer
            except StripeError:
                logger.error('Error retrieving Stripe customer %s' % user.userprofile.stripe_customer_id)
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
        # Data from https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(PPP)_per_capita
        countries_sorted_by_gdp_per_capita = [
            "LI",  # Liechtenstein
            "LU",  # Luxembourg
            "MC",  # Monaco
            "SG",  # Singapore
            "IE",  # Ireland
            "QA",  # Qatar
            "IM",  # Isle of Man
            "BM",  # Bermuda
            "CH",  # Switzerland
            "FK",  # Falkland Islands
            "AE",  # United Arab Emirates
            "KY",  # Cayman Islands
            "NO",  # Norway
            "MO",  # Macau
            "US",  # United States
            "GI",  # Gibraltar
            "BN",  # Brunei
            "HK",  # Hong Kong
            "DK",  # Denmark
            "NL",  # Netherlands
            "JE",  # Jersey
            "SM",  # San Marino
            "AT",  # Austria
            "IS",  # Iceland
            "SE",  # Sweden
            "DE",  # Germany
            "GG",  # Guernsey
            "BE",  # Belgium
            "TW",  # Taiwan
            "AD",  # Andorra
            "AU",  # Australia
            "BH",  # Bahrain
            "FI",  # Finland
            "CA",  # Canada
            "PM",  # Saint Pierre and Miquelon
            "FR",  # France
            "GB",  # United Kingdom
            "MT",  # Malta
            "SA",  # Saudi Arabia
            "KR",  # South Korea
            "KW",  # Kuwait
            "NZ",  # New Zealand
            "IL",  # Israel
            "IT",  # Italy
            "GL",  # Greenland
            "CY",  # Cyprus
            "JP",  # Japan
            "CZ",  # Czech Republic
            "SI",  # Slovenia
            "FO",  # Faroe Islands
            "LT",  # Lithuania
            "AW",  # Aruba
            "EE",  # Estonia
            "ES",  # Spain
            "VI",  # U.S. Virgin Islands
            "GU",  # Guam
            "SX",  # Sint Maarten (Dutch part)
            "PL",  # Poland
            "OM",  # Oman
            "VG",  # British Virgin Islands
            "MS",  # Montserrat
            "PT",  # Portugal
            "HU",  # Hungary
            "PR",  # Puerto Rico
            "LV",  # Latvia
            "SK",  # Slovakia
            "HR",  # Croatia
            "TR",  # Turkey
            "NC",  # New Caledonia
            "RO",  # Romania
            "BS",  # Bahamas
            "GR",  # Greece
            "PA",  # Panama
            "SC",  # Seychelles
            "RU",  # Russia
            "KN",  # Saint Kitts and Nevis
            "MY",  # Malaysia
            "KZ",  # Kazakhstan
            "CL",  # Chile
            "MP",  # Northern Mariana Islands
            "BG",  # Bulgaria
            "TT",  # Trinidad and Tobago
            "UY",  # Uruguay
            "LY",  # Libya
            "GY",  # Guyana
            "AR",  # Argentina
            "CR",  # Costa Rica
            "MU",  # Mauritius
            "CW",  # Curaçao
            "ME",  # Montenegro
            "RS",  # Serbia
            "BY",  # Belarus
            "MF",  # Saint Martin (French part)
            "AG",  # Antigua and Barbuda
            "MX",  # Mexico
            "MV",  # Maldives
            "DO",  # Dominican Republic
            "TC",  # Turks and Caicos Islands
            "CN",  # China
            "TH",  # Thailand
            "PF",  # French Polynesia
            "CK",  # Cook Islands
            "MK",  # North Macedonia
            "BA",  # Bosnia and Herzegovina
            "GE",  # Georgia
            "TM",  # Turkmenistan
            "BW",  # Botswana
            "SR",  # Suriname
            "CO",  # Colombia
            "GQ",  # Equatorial Guinea
            "AL",  # Albania
            "AZ",  # Azerbaijan
            "AM",  # Armenia
            "BR",  # Brazil
            "MD",  # Moldova
            "GA",  # Gabon
            "BB",  # Barbados
            "PW",  # Palau
            "GD",  # Grenada
            "VC",  # Saint Vincent and the Grenadines
            "PY",  # Paraguay
            "LK",  # Sri Lanka
            "ZA",  # South Africa
            "LC",  # Saint Lucia
            "LB",  # Lebanon
            "UA",  # Ukraine
            "PE",  # Peru
            "IR",  # Iran
            "CU",  # Cuba
            "AI",  # Anguilla
            "ID",  # Indonesia
            "XK",  # Kosovo
            "NR",  # Nauru
            "MN",  # Mongolia
            "EG",  # Egypt
            "AS",  # American Samoa
            "DZ",  # Algeria
            "BT",  # Bhutan
            "DM",  # Dominica
            "EC",  # Ecuador
            "VN",  # Vietnam
            "FJ",  # Fiji
            "TN",  # Tunisia
            "JM",  # Jamaica
            "JO",  # Jordan
            "SV",  # El Salvador
            "NA",  # Namibia
            "IQ",  # Iraq
            "SZ",  # Eswatini
            "GT",  # Guatemala
            "BZ",  # Belize
            "PH",  # Philippines
            "MA",  # Morocco
            "BO",  # Bolivia
            "LA",  # Laos
            "SH",  # Saint Helena
            "VE",  # Venezuela
            "UZ",  # Uzbekistan
            "IN",  # India
            "CV",  # Cape Verde
            "TO",  # Tonga
            "TK",  # Tokelau
            "MH",  # Marshall Islands
            "BD",  # Bangladesh
            "AO",  # Angola
            "NU",  # Niue
            "NI",  # Nicaragua
            "HN",  # Honduras
            "PS",  # Palestine
            "WS",  # Samoa
            "GH",  # Ghana
            "MR",  # Mauritania
            "CI",  # Ivory Coast
            "PK",  # Pakistan
            "TL",  # East Timor
            "DJ",  # Djibouti
            "NG",  # Nigeria
            "TV",  # Tuvalu
            "KG",  # Kyrgyzstan
            "KE",  # Kenya
            "KH",  # Cambodia
            "MM",  # Myanmar
            "ST",  # São Tomé and Príncipe
            "TJ",  # Tajikistan
            "NP",  # Nepal
            "WF",  # Wallis and Futuna
            "CM",  # Cameroon
            "PG",  # Papua New Guinea
            "SD",  # Sudan
            "SN",  # Senegal
            "BJ",  # Benin
            "FM",  # Micronesia
            "CG",  # Congo
            "ZM",  # Zambia
            "KM",  # Comoros
            "HT",  # Haiti
            "SY",  # Syria
            "VU",  # Vanuatu
            "TZ",  # Tanzania
            "GN",  # Guinea
            "YE",  # Yemen
            "SB",  # Solomon Islands
            "ET",  # Ethiopia
            "LS",  # Lesotho
            "UG",  # Uganda
            "RW",  # Rwanda
            "BF",  # Burkina Faso
            "GM",  # Gambia
            "TG",  # Togo
            "ML",  # Mali
            "ZW",  # Zimbabwe
            "KI",  # Kiribati
            "GW",  # Guinea-Bissau
            "KP",  # North Korea
            "ER",  # Eritrea
            "SL",  # Sierra Leone
            "SS",  # South Sudan
            "AF",  # Afghanistan
            "MG",  # Madagascar
            "MW",  # Malawi
            "LR",  # Liberia
            "TD",  # Chad
            "NE",  # Niger
            "MZ",  # Mozambique
            "CD",  # DR Congo
            "SO",  # Somalia
            "CF",  # Central African Republic
            "BI"  # Burundi
        ]

        total_countries = len(countries_sorted_by_gdp_per_capita)

        tier_1 = countries_sorted_by_gdp_per_capita[:total_countries // 4] # Top 25% of countries
        tier_2 = countries_sorted_by_gdp_per_capita[total_countries // 4:total_countries // 2] # Then 25% of countries
        tier_3 = countries_sorted_by_gdp_per_capita[total_countries // 2:] # Bottom 50% of countries

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

    @staticmethod
    def get_user_country_code(user, request) -> str:
        # When it comes to pricing, we use the user's signup country when available.
        country_code = user.userprofile.signup_country or get_client_country_code(request) or 'us'
        country_code = country_code.lower() if country_code != 'UNKNOWN' else 'us'
        return country_code
