import os

SUBSCRIPTION_GRACE_PERIOD = 0

# Only used in donations form
SUBSCRIPTION_PAYPAL_SETTINGS = {
    'business': 'paypal@astrobin.com'
}

PAYPAL_TEST = os.environ.get('PAYPAL_TEST', 'false') == 'true'

# Used for the "Cancel subscription" link
PAYPAL_MERCHANT_ID = os.environ.get('PAYPAL_MERCHANT_ID', 'invalid').strip()

