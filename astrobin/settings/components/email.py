import os

SEND_EMAILS = os.environ.get('SEND_EMAILS', 'false').strip()

if SEND_EMAILS == 'true':
    EMAIL_BACKEND = 'astrobin.custom_celery_email_backend.CustomCeleryEmailBackend'
    CELERY_EMAIL_BACKEND = 'astrobin.custom_email_backend.CustomEmailBackend'

    CELERY_EMAIL_TASK_CONFIG = {
        'queue': 'email',
        'delivery_mode': 1,  # non persistent
        'rate_limit': '150/m',  # 15 chunks per minute
    }

    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost').strip()
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '').strip()
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '').strip()
    EMAIL_PORT = int(os.environ.get('EMAIL_HOST_PORT', '25').strip())
    EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'false').strip() == 'true'
elif SEND_EMAILS == 'dev':
    EMAIL_BACKEND = 'astrobin.custom_email_backend.CustomEmailBackend'

    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost').strip()
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '').strip()
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '').strip()
    EMAIL_PORT = int(os.environ.get('EMAIL_HOST_PORT', '25').strip())
    EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'false').strip() == 'true'

    EMAIL_DEV_RECIPIENT = os.environ.get('EMAIL_DEV_RECIPIENT', 'astrobin@astrobin.com')
elif SEND_EMAILS == 'dummy':
    EMAIL_BACKEND = 'astrobin.custom_email_backend.CustomEmailBackend'

    EMAIL_HOST = 'debug_email'
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
    EMAIL_PORT = 25
    EMAIL_USE_SSL = False
else:
    EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

SERVER_EMAIL = DEFAULT_FROM_EMAIL = OTP_EMAIL_SENDER = os.environ.get('SERVER_EMAIL', 'noreply@astrobin.com').strip()
EMAIL_SUBJECT_PREFIX = os.environ.get('EMAIL_SUBJECT_PREFIX', '[AstroBin]').strip()

BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '').strip()
BREVO_NEWSLETTER_LIST_ID = os.environ.get('BREVO_NEWSLETTER_LIST_ID', 0).strip()
