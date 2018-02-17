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

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@astrobin.com')
EMAIL_SUBJECT_PREFIX = os.environ.get('EMAIL_SUBJECT_PREFIX', '[AstroBin]')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', 'noreply@astrobin.com')

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'postfix')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'astrobin')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'astrobin')
EMAIL_PORT = os.environ.get('EMAIL_HOST_PORT', 465)
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'true') == 'true'

