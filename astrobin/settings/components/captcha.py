TURNSTILE_TEST_SITE_KEY = '1x00000000000000000000AA'
TURNSTILE_TEST_SECRET_KEY = '1x0000000000000000000000000000000AA'

if DEBUG or TESTING:
    TURNSTILE_SITE_KEY = TURNSTILE_TEST_SITE_KEY
    TURNSTILE_SECRET_KEY = TURNSTILE_TEST_SECRET_KEY
else:
    import os
    TURNSTILE_SITE_KEY = os.environ.get('TURNSTILE_SITE_KEY', TURNSTILE_TEST_SITE_KEY)
    TURNSTILE_SECRET_KEY = os.environ.get('TURNSTILE_SECRET_KEY', TURNSTILE_TEST_SECRET_KEY)
