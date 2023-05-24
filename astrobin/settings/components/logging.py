import os

from boto3.session import Session

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', 'invalid').strip()
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', 'invalid').strip()
AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME', 'us-east-1').strip()
CLOUDWATCH_LOGGING_ENABLED = os.environ.get('CLOUDWATCH_LOGGING_ENABLED', 'false').strip() == 'true'

# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },

        'aws': {
            'format': "[%(levelname)s] [%(name)s] %(message)s",
            'datefmt': "%Y-%m-%d %H:%M:%S"
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "debug.log",
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'ERROR',
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'werkzeug': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'elasticsearch': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'urllib3': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'boto3': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        's3transfer': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'PIL': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'celery.evcam': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django_bouncy': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'stripe': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}

if DEBUG:
    for logger_name, logger_config in LOGGING['loggers'].items():
        LOGGING['loggers'][logger_name]['handlers'].append('logfile')

if AWS_ACCESS_KEY_ID != 'invalid' and \
        AWS_SECRET_ACCESS_KEY != 'invalid' and \
        CLOUDWATCH_LOGGING_ENABLED and \
        'localhost' not in BASE_URL:
    boto3_session = Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                            region_name=AWS_REGION_NAME)

    LOGGING['handlers']['watchtower'] = {
        'level': 'DEBUG',
        'class': 'watchtower.CloudWatchLogHandler',
        'boto3_session': boto3_session,
        'log_group': 'astrobin',
        'stream_name': BASE_URL.replace('https://', '').replace('http://', ''),
        'formatter': 'aws',
    }

    for logger_name, logger_config in LOGGING['loggers'].items():
        LOGGING['loggers'][logger_name]['handlers'].append('watchtower')
