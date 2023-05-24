import os

SUPPORTED_CURRENCIES = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'CHF', 'CNY']
TRANSFERWISE_API_TOKEN = os.environ.get('TRANSFERWISE_API_TOKEN')

def test_or_live(key: str) -> str:
    return os.environ.get(key.replace('XXXX', 'TEST' if DEBUG or TESTING else 'LIVE'))

STRIPE = {
    'keys': {
        'publishable': test_or_live('STRIPE_PUBLISHABLE_KEY_XXXX'),
        'secret': test_or_live('STRIPE_SECRET_KEY_XXXX'),
        'endpoint-secret': test_or_live('STRIPE_ENDPOINT_SECRET_XXXX'),
        'customer-portal-key': test_or_live('STRIPE_CUSTOMER_PORTAL_KEY_XXXX'),
    },
    'products': {
        'lite': test_or_live('STRIPE_PRODUCT_LITE_XXXX'),
        'premium': test_or_live('STRIPE_PRODUCT_PREMIUM_XXXX'),
        'ultimate': test_or_live('STRIPE_PRODUCT_ULTIMATE_XXXX'),
    },
    'prices': {
        'lite': {
            'monthly-tier-1': test_or_live('STRIPE_PRICE_LITE_MONTHLY_TIER_1_XXXX'),
            'yearly-tier-1': test_or_live('STRIPE_PRICE_LITE_YEARLY_TIER_1_XXXX'),
            'one-year-tier-1': test_or_live('STRIPE_PRICE_LITE_ONE_YEAR_TIER_1_XXXX'),
            'monthly-tier-2': test_or_live('STRIPE_PRICE_LITE_MONTHLY_TIER_2_XXXX'),
            'yearly-tier-2': test_or_live('STRIPE_PRICE_LITE_YEARLY_TIER_2_XXXX'),
            'one-year-tier-2': test_or_live('STRIPE_PRICE_LITE_ONE_YEAR_TIER_2_XXXX'),
            'monthly-tier-3': test_or_live('STRIPE_PRICE_LITE_MONTHLY_TIER_3_XXXX'),
            'yearly-tier-3': test_or_live('STRIPE_PRICE_LITE_YEARLY_TIER_3_XXXX'),
            'one-year-tier-3': test_or_live('STRIPE_PRICE_LITE_ONE_YEAR_TIER_3_XXXX'),
        },
        'premium': {
            'monthly-tier-1': test_or_live('STRIPE_PRICE_PREMIUM_MONTHLY_TIER_1_XXXX'),
            'yearly-tier-1': test_or_live('STRIPE_PRICE_PREMIUM_YEARLY_TIER_1_XXXX'),
            'one-year-tier-1': test_or_live('STRIPE_PRICE_PREMIUM_ONE_YEAR_TIER_1_XXXX'),
            'monthly-tier-2': test_or_live('STRIPE_PRICE_PREMIUM_MONTHLY_TIER_2_XXXX'),
            'yearly-tier-2': test_or_live('STRIPE_PRICE_PREMIUM_YEARLY_TIER_2_XXXX'),
            'one-year-tier-2': test_or_live('STRIPE_PRICE_PREMIUM_ONE_YEAR_TIER_2_XXXX'),
            'monthly-tier-3': test_or_live('STRIPE_PRICE_PREMIUM_MONTHLY_TIER_3_XXXX'),
            'yearly-tier-3': test_or_live('STRIPE_PRICE_PREMIUM_YEARLY_TIER_3_XXXX'),
            'one-year-tier-3': test_or_live('STRIPE_PRICE_PREMIUM_ONE_YEAR_TIER_3_XXXX'),
        },
        'ultimate': {
            'monthly-tier-1': test_or_live('STRIPE_PRICE_ULTIMATE_MONTHLY_TIER_1_XXXX'),
            'yearly-tier-1': test_or_live('STRIPE_PRICE_ULTIMATE_YEARLY_TIER_1_XXXX'),
            'one-year-tier-1': test_or_live('STRIPE_PRICE_ULTIMATE_ONE_YEAR_TIER_1_XXXX'),
            'monthly-tier-2': test_or_live('STRIPE_PRICE_ULTIMATE_MONTHLY_TIER_2_XXXX'),
            'yearly-tier-2': test_or_live('STRIPE_PRICE_ULTIMATE_YEARLY_TIER_2_XXXX'),
            'one-year-tier-2': test_or_live('STRIPE_PRICE_ULTIMATE_ONE_YEAR_TIER_2_XXXX'),
            'monthly-tier-3': test_or_live('STRIPE_PRICE_ULTIMATE_MONTHLY_TIER_3_XXXX'),
            'yearly-tier-3': test_or_live('STRIPE_PRICE_ULTIMATE_YEARLY_TIER_3_XXXX'),
            'one-year-tier-3': test_or_live('STRIPE_PRICE_ULTIMATE_ONE_YEAR_TIER_3_XXXX'),
        },
    },
}
