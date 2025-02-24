REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticatedOrReadOnly',),
    'PAGE_SIZE': 50,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Useful for unit tests
    ),
    'DEFAULT_THROTTLE_CLASSES': ['astrobin.api2.throttle.MultiRateThrottle'],
}

MULTI_THROTTLE_RATES = {
    'anon': {
        'read': ["20/10s", "150/60s", "500/5min"],
        'write': ["40/60s", "200/5min"],
    },
    'user': {
        'read': ["40/10s", "300/60s", "1000/5min"],
        'write': ["60/60s", "300/5min"],
    },
    'premium': {
        'read': ["50/10s", "500/60s", "2000/5min"],
        'write': ["100/60s", "500/5min"],
    },
}
