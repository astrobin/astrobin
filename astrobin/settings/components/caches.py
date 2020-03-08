import os

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '%s:11211' % os.environ.get('MEMCACHED_HOST', 'memcached').strip(),
    },
}

JOHNNY_MIDDLEWARE_KEY_PREFIX='jc_astrobin'

