if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

    EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

