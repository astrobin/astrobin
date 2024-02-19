import os

CACHE_TYPE = os.environ.get('CACHE_TYPE', 'redis').strip()

if CACHE_TYPE == 'redis':
    CACHES = {
        'default': {
            'BACKEND': 'astrobin.custom_redis_cache.CustomRedisCache',
            'LOCATION': os.environ.get('CACHE_URL', 'redis://redis:6379/1').strip(),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'PICKLE_VERSION': 5,
                'PARSER_CLASS': 'redis.connection._HiredisParser',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 100,
                },
                'SOCKET_TIMEOUT': 0.05,
                'SOCKET_CONNECT_TIMEOUT': 0.05,
            },
            'KEY_PREFIX': 'astrobin',
            'TIMEOUT': 3600,
        },
        'json': {
            'BACKEND': 'astrobin.custom_redis_cache.CustomRedisCache',
            'LOCATION': os.environ.get('CACHE_URL_JSON', 'redis://redis:6379/3').strip(),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 100,
                },
                'SOCKET_TIMEOUT': 0.05,
                'SOCKET_CONNECT_TIMEOUT': 0.05,
            },
            'KEY_PREFIX': 'astrobin',
            'TIMEOUT': 3600,
        },
    }
elif CACHE_TYPE == 'locmem':
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        },
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        },
    }
