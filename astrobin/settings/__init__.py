import os

from split_settings.tools import optional, include

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
include(
    # Begin
    'components/basic.py',

    # Django settings
    'components/admins.py',
    'components/ads.py',
    'components/apps.py',
    'components/caches.py',
    'components/cookies.py',
    'components/cors.py',
    'components/db.py',
    'components/email.py',
    'components/google.py',
    'components/languages.py',
    'components/logging.py',
    'components/middleware.py',
    'components/session.py',
    'components/storage.py',
    'components/templates.py',
    'components/cloudflare.py',
    'components/cloudfront.py',

    # Apps settings
    'components/account.py',
    'components/actstream.py',
    'components/avatar.py',
    'components/captcha.py',
    'components/celery.py',
    'components/forum.py',
    'components/haystack.py',
    'components/hitcount.py',
    'components/notification.py',
    'components/pagination.py',
    'components/pipeline.py',
    'components/privatebeta.py',
    'components/rest.py',
    'components/subscription.py',
    'components/tinymce.py',
    'components/thumbnail.py',
    'components/toggleproperties.py',
    'components/robots.py',
    'components/sentry.py',

    # AstroBin settings
    'components/flickr.py',
    'components/iotd.py',
    'components/platesolving.py',
    'components/premium.py',
    'components/payments.py',

    # Environments
    'environments/debug.py',
    'environments/testing.py',

    # Locally overridden settings
    optional('local_settings.py')
)

