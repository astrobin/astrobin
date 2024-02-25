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
        },
        'reader': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'astrobin_test_db',
        },
        'segregated_reader': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'astrobin_test_db',
        }
    }

    MIGRATION_MODULES = {
        app.split('.')[-1]: None for app in INSTALLED_APPS if app not in [
            # https://stackoverflow.com/questions/73104958/no-such-table-two-factor-phonedevice-when-using-django-two-factor-auth-1-14-0
            'two_factor'
        ]
    }

    MIGRATION_MODULES['astrobin'] = None
    MIGRATION_MODULES['astrobin_apps_equipment'] = None
    MIGRATION_MODULES['astrobin_apps_iotd'] = None
    MIGRATION_MODULES['astrobin_apps_images'] = None

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        },
        'json': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        },
    }

    MIDDLEWARE = [
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]

    EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

    logging.disable(logging.CRITICAL)

    PREMIUM_MAX_IMAGES_FREE = 20
    PREMIUM_MAX_IMAGES_LITE = 20

    CELERY_ALWAYS_EAGER = True
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_RESULT_BACKEND = 'cache'
    CELERY_CACHE_BACKEND = 'memory'

    STATICFILES_STORAGE = 'pipeline.storage.NonPackagingPipelineStorage'
