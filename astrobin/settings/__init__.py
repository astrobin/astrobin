import os

from split_settings.tools import optional, include

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

include(
    # Begin
    'components/basic.py',

    # Django settings
    'components/admins.py',
    'components/apps.py',
    'components/caches.py',
    'components/db.py',
    'components/email.py',
    'components/languages.py',
    'components/logging.py',
    'components/middleware.py',
    'components/session.py',
    'components/storage.py',
    'components/templates.py',

    # Apps settings
    'components/account.py',
    'components/avatar.py',
    'components/celery.py',
    'components/haystack.py',
    'components/hitcount.py',
    'components/notification.py',
    'components/pagination.py',
    'components/pipeline.py',
    'components/privatebeta.py',
    'components/pybb.py',
    'components/rest.py',
    'components/silky.py',
    'components/subscription.py',
    'components/tinymce.py',
    'components/thumbnail.py',
    'components/toggleproperties.py',
    'components/webpack-loader.py',

    # AstroBin settings
    'components/flickr.py',
    'components/iotd.py',
    'components/platesolving.py',
    'components/premium.py',

    # Environments
    'environments/debug.py',
    'environments/testing.py',

    # Locally overriden settings
    optional('local_settings.py')
)
