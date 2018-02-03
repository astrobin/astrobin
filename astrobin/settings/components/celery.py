BROKER_URL = 'amqp://astrobin:%s@queue:5672' % os.environ['RABBITMQ_DEFAULT_PASS']
BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,
    'fanout_prefix': True,
    'fanout_patterns': True,
}
CELERY_RESULT_BACKEND = 'cache+memcached://cache:11211/'
CELERY_IMPORTS = ('astrobin.tasks', 'rawdata.tasks',)
CELERY_QUEUES = {"default" : {"exchange":"default", "binding_key":"default"},}
CELERY_DEFAULT_QUEUE = "default"
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_TASK_SERIALIZER = 'pickle'

