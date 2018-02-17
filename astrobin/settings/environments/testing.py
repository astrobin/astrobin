import sys
import logging

TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

if TESTING:
    DEBUG = False
    AWS_S3_ENABLED = False
    LOCAL_STATIC_STORAGE = True

    PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
    )

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'astrobin_test_db',
        }
    }

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

    EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

    logging.disable(logging.CRITICAL)

    PREMIUM_MAX_IMAGES_FREE = 20
    PREMIUM_MAX_IMAGES_LITE = 20

