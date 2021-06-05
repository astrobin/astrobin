import os

CACHE_TYPE = os.environ.get('CACHE_TYPE', 'redis').strip()

if CACHE_TYPE == 'redis':
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.environ.get('BROKER_URL', 'redis://redis:6379/0').strip(),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient'
            },
            'KEY_PREFIX': 'astrobin'
        }
    }
elif CACHE_TYPE == 'locmem':
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

CACHALOT_ENABLED = os.environ.get('CACHALOT_ENABLED', 'false').strip() == 'true'
