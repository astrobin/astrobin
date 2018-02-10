import os

EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
CELERY_EMAIL_TASK_CONFIG = {
    'queue': 'default',
    'delivery_mode': 1,  # non persistent
    'rate_limit': '50/m',  # 50 chunks per minute
}

if os.environ.get('SEND_EMAILS', 'true') == 'true':
    CELERY_EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    CELERY_EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

DEFAULT_FROM_EMAIL = os.environ['DEFAULT_FROM_EMAIL']
EMAIL_SUBJECT_PREFIX = os.environ['EMAIL_SUBJECT_PREFIX']
SERVER_EMAIL = os.environ['SERVER_EMAIL']

EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
EMAIL_PORT = os.environ['EMAIL_HOST_PORT']
EMAIL_USE_SSL = os.environ['EMAIL_USE_SSL'] == 'true'

