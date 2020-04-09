import os
import sys
import logging

if TESTING:
    DEBUG = False
    AWS_S3_ENABLED = False
    LOCAL_STATIC_STORAGE = True
    PREMIUM_ENABLED = True

    PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
    )

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'astrobin_test_db',
        }
    }

    MIGRATION_MODULES = {
        app.split('.')[-1]: None for app in INSTALLED_APPS
    }

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

    MIDDLEWARE_CLASSES = [
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'gadjo.requestprovider.middleware.RequestProvider',
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]

    EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

    logging.disable(logging.CRITICAL)

    PREMIUM_MAX_IMAGES_FREE = 20
    PREMIUM_MAX_IMAGES_LITE = 20

    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_RESULT_BACKEND = 'cache'
    CELERY_CACHE_BACKEND = 'memory'

    STATICFILES_STORAGE = 'pipeline.storage.NonPackagingPipelineStorage'
