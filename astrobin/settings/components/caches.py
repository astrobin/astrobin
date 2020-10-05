import os

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '%s:11211' % os.environ.get('MEMCACHED_HOST', 'memcached').strip(),
    },
}

CACHALOT_ENABLED = os.environ.get('CACHALOT_ENABLED', 'false').strip() == 'true'
