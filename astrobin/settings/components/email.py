import os


if os.environ.get('SEND_EMAILS', 'false') == 'true':
    EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
    CELERY_EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

    CELERY_EMAIL_TASK_CONFIG = {
        'queue': 'email',
        'delivery_mode': 1,  # non persistent
        'rate_limit': '30/m',  # 50 chunks per minute
    }

    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    EMAIL_PORT = os.environ.get('EMAIL_HOST_PORT', 25)
    EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'false') == 'true'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

    EMAIL_HOST = 'debug_email'
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
    EMAIL_PORT = 25
    EMAIL_USE_SSL = False

SERVER_EMAIL = DEFAULT_FROM_EMAIL = os.environ.get('SERVER_EMAIL', 'noreply@astrobin.com')
EMAIL_SUBJECT_PREFIX = os.environ.get('EMAIL_SUBJECT_PREFIX', '[AstroBin]')


