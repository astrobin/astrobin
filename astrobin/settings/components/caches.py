import os

CACHE_TYPE = os.environ.get('CACHE_TYPE', 'memcached').strip()

if CACHE_TYPE == 'memcached':
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '%s:11211' % os.environ.get('MEMCACHED_HOST', 'memcached').strip(),
        },
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
