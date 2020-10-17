import os
from kombu import Exchange, Queue


BROKER_URL = os.environ.get('BROKER_URL', 'amqp://astrobin:astrobin@rabbitmq:5672').strip()
BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,
    'fanout_prefix': True,
    'fanout_patterns': True,
}
CELERY_RESULT_BACKEND = 'cache+memcached://memcached:11211/'
CELERY_IMPORTS = ('astrobin.tasks', 'djcelery_email.tasks')
CELERY_DEFAULT_QUEUE = 'main'
CELERY_HAYSTACK_QUEUE = 'haystack'
CELERY_ACCEPT_CONTENT = ['pickle', 'json']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = TIME_ZONE
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100

CELERY_QUEUES = (
    Queue('main', Exchange('main'), routing_key='main'),
    Queue('email', Exchange('email'), routing_key='email'),
    Queue('haystack', Exchange('haystack'), routing_key='haystack'),
    Queue('thumbnails', Exchange('thumbnails'), routing_key='thumbnails'),
)
CELERY_ROUTES = {
    'astrobin.tasks.retrieve_thumbnail': {
        'queue': 'thumbnails',
        'routing_key': 'thumbnails',
    },
    'astrobin.tasks.retrieve_primary_thumbnails': {
        'queue': 'thumbnails',
        'routing_key': 'thumbnails',
    },
    'astrobin.tasks.send_broadcast_email': {
        'queue': 'email',
        'routing_key': 'email',
    },
    'celery_haystack.tasks.CeleryHaystackSignalHandler': {
        'queue': 'haystack',
        'routing_key': 'haystack',
    },
    'celery_haystack.tasks.CeleryHaystackUpdateIndex': {
        'queue': 'haystack',
        'routing_key': 'haystack',
    },
    'djcelery_email_send_multiple': {
        'queue': 'email',
        'routing_key': 'email',
    },

}
