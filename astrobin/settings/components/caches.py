CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'memcached:11211',
    },
}

JOHNNY_MIDDLEWARE_KEY_PREFIX = 'jc_astrobin'
