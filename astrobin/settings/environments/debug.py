if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

    PYBB_ANONYMOUS_VIEWS_CACHE_BUFFER = 0

