CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
    'HEAD'
]
CORS_ALLOW_HEADERS = [
    'x-requested-with',
    'content-type',
    'content-disposition',
    'accept',
    'origin',
    'authorization',
    'x-csrftoken',
    'user-agent',
    'accept-encoding',
    'cache-control',
    'tus-resumable',
    'upload-length',
    'upload-metadata',
    'upload-offset',
    'location',
    'sentry-trace',
    'baggage',
]
CORS_EXPOSE_HEADERS = CORS_ALLOW_HEADERS
CORS_ALLOW_CREDENTIALS = True
