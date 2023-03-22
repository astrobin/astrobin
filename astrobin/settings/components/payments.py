import os

SUPPORTED_CURRENCIES = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'CHF', 'CNY']
TRANSFERWISE_API_TOKEN = os.environ.get('TRANSFERWISE_API_TOKEN')

def test_or_live(key: str) -> str:
    return os.environ.get(key.replace('XXXX', 'TEST' if DEBUG or TESTING else 'LIVE'))

STRIPE = {
    'keys': {
        'publishable': test_or_live('STRIPE_PUBLISHABLE_XXXX_KEY'),
        'secret': test_or_live('STRIPE_SECRET_XXXX_KEY'),
        'endpoint-secret': test_or_live('STRIPE_ENDPOINT_SECRET_XXXX'),
    },
    'products': {
        'non-recurring': {
            'lite': test_or_live('STRIPE_PRODUCT_LITE_XXXX'),
            'premium': test_or_live('STRIPE_PRODUCT_PREMIUM_XXXX'),
            'ultimate': test_or_live('STRIPE_PRODUCT_ULTIMATE_XXXX'),
        },
        'recurring': {
            'lite': test_or_live('STRIPE_PRODUCT_LITE_RECURRING_XXXX'),
            'premium': test_or_live('STRIPE_PRODUCT_PREMIUM_RECURRING_XXXX'),
            'ultimate': test_or_live('STRIPE_PRODUCT_ULTIMATE_RECURRING_XXXX'),
        },
    },
    'prices': {
        'non-recurring': {
            'lite': {
                'monthly': test_or_live('STRIPE_PRICE_LITE_MONTHLY_XXXX'),
                'yearly': test_or_live('STRIPE_PRICE_LITE_YEARLY_XXXX'),
            },
            'premium': {
                'monthly': test_or_live('STRIPE_PRICE_PREMIUM_MONTHLY_XXXX'),
                'yearly': test_or_live('STRIPE_PRICE_PREMIUM_YEARLY_XXXX'),
            },
            'ultimate': {
                'monthly': test_or_live('STRIPE_PRICE_ULTIMATE_MONTHLY_XXXX'),
                'yearly': test_or_live('STRIPE_PRICE_ULTIMATE_YEARLY_XXXX'),
            },
        },
        'recurring': {
            'lite': {
                'monthly': test_or_live('STRIPE_PRICE_LITE_MONTHLY_RECURRING_XXXX'),
                'yearly': test_or_live('STRIPE_PRICE_LITE_YEARLY_RECURRING_XXXX'),
            },
            'premium': {
                'monthly': test_or_live('STRIPE_PRICE_PREMIUM_MONTHLY_RECURRING_XXXX'),
                'yearly': test_or_live('STRIPE_PRICE_PREMIUM_YEARLY_RECURRING_XXXX'),
            },
            'ultimate': {
                'monthly': test_or_live('STRIPE_PRICE_ULTIMATE_MONTHLY_RECURRING_XXXX'),
                'yearly': test_or_live('STRIPE_PRICE_ULTIMATE_YEARLY_RECURRING_XXXX'),
            },
        },
    },
}
