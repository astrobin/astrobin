import os

if DEBUG or TESTING:
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_TEST_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_TEST_KEY')
    STRIPE_ENDPOINT_SECRET = os.environ.get('STRIPE_ENDPOINT_SECRET_TEST')

    STRIPE_PRICE_LITE = {
        "USD": os.environ.get('STRIPE_PRICE_TEST_LITE_USD'),
        "EUR": os.environ.get('STRIPE_PRICE_TEST_LITE_EUR'),
        "GBP": os.environ.get('STRIPE_PRICE_TEST_LITE_GBP'),
        "CAD": os.environ.get('STRIPE_PRICE_TEST_LITE_CAD'),
        "AUD": os.environ.get('STRIPE_PRICE_TEST_LITE_AUD'),
        "CHF": os.environ.get('STRIPE_PRICE_TEST_LITE_CHF'),
    }
    
    STRIPE_PRICE_PREMIUM = {
        "USD": os.environ.get('STRIPE_PRICE_TEST_PREMIUM_USD'),
        "EUR": os.environ.get('STRIPE_PRICE_TEST_PREMIUM_EUR'),
        "GBP": os.environ.get('STRIPE_PRICE_TEST_PREMIUM_GBP'),
        "CAD": os.environ.get('STRIPE_PRICE_TEST_PREMIUM_CAD'),
        "AUD": os.environ.get('STRIPE_PRICE_TEST_PREMIUM_AUD'),
        "CHF": os.environ.get('STRIPE_PRICE_TEST_PREMIUM_CHF'),
    }
    
    STRIPE_PRICE_ULTIMATE = {
        "USD": os.environ.get('STRIPE_PRICE_TEST_ULTIMATE_USD'),
        "EUR": os.environ.get('STRIPE_PRICE_TEST_ULTIMATE_EUR'),
        "GBP": os.environ.get('STRIPE_PRICE_TEST_ULTIMATE_GBP'),
        "CAD": os.environ.get('STRIPE_PRICE_TEST_ULTIMATE_CAD'),
        "AUD": os.environ.get('STRIPE_PRICE_TEST_ULTIMATE_AUD'),
        "CHF": os.environ.get('STRIPE_PRICE_TEST_ULTIMATE_CHF'),
    }
else:
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_LIVE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_LIVE_KEY')
    STRIPE_ENDPOINT_SECRET = os.environ.get('STRIPE_ENDPOINT_SECRET_LIVE')

    STRIPE_PRICE_LITE = {
        "USD": os.environ.get('STRIPE_PRICE_LIVE_LITE_USD'),
        "EUR": os.environ.get('STRIPE_PRICE_LIVE_LITE_EUR'),
        "GBP": os.environ.get('STRIPE_PRICE_LIVE_LITE_GBP'),
        "CAD": os.environ.get('STRIPE_PRICE_LIVE_LITE_CAD'),
        "AUD": os.environ.get('STRIPE_PRICE_LIVE_LITE_AUD'),
        "CHF": os.environ.get('STRIPE_PRICE_LIVE_LITE_CHF'),
    }

    STRIPE_PRICE_PREMIUM = {
        "USD": os.environ.get('STRIPE_PRICE_LIVE_PREMIUM_USD'),
        "EUR": os.environ.get('STRIPE_PRICE_LIVE_PREMIUM_EUR'),
        "GBP": os.environ.get('STRIPE_PRICE_LIVE_PREMIUM_GBP'),
        "CAD": os.environ.get('STRIPE_PRICE_LIVE_PREMIUM_CAD'),
        "AUD": os.environ.get('STRIPE_PRICE_LIVE_PREMIUM_AUD'),
        "CHF": os.environ.get('STRIPE_PRICE_LIVE_PREMIUM_CHF'),
    }

    STRIPE_PRICE_ULTIMATE = {
        "USD": os.environ.get('STRIPE_PRICE_LIVE_ULTIMATE_USD'),
        "EUR": os.environ.get('STRIPE_PRICE_LIVE_ULTIMATE_EUR'),
        "GBP": os.environ.get('STRIPE_PRICE_LIVE_ULTIMATE_GBP'),
        "CAD": os.environ.get('STRIPE_PRICE_LIVE_ULTIMATE_CAD'),
        "AUD": os.environ.get('STRIPE_PRICE_LIVE_ULTIMATE_AUD'),
        "CHF": os.environ.get('STRIPE_PRICE_LIVE_ULTIMATE_CHF'),
    }
