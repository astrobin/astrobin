import os

from elasticsearch import RequestsHttpConnection
from requests_aws4auth import AWS4Auth

HAYSTACK_DEFAULT_OPERATOR = 'AND'
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 70

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': os.environ.get('ELASTICSEARCH_URL', 'http://elasticsearch'),
        'INDEX_NAME': 'astrobin',
        'EXCLUDED_INDEXES': [
            'threaded_messages.search_indexes.Thread',
            'threaded_messages.search_indexes.ThreadIndex',
        ]
    },
}

if 'es.amazonaws.com' in HAYSTACK_CONNECTIONS['default']['URL']:
    HAYSTACK_CONNECTIONS['default']['KWARGS'] = {
        'port': 443,
        'http_auth': AWS4Auth(
            os.environ.get('AWS_ACCESS_KEY_ID'),
            os.environ.get('AWS_SECRET_ACCESS_KEY'),
            os.environ.get('ELASTIC_SEARCH_AWS_REGION', 'us-east-1'),
            'es'),
        'use_ssl': True,
        'verify_certs': True,
        'connection_class': RequestsHttpConnection,
    }
else:
    HAYSTACK_CONNECTIONS['default']['KWARGS'] = {
        'port': 9200
    }

if not TESTING:
    HAYSTACK_SIGNAL_PROCESSOR = 'celery_haystack.signals.CelerySignalProcessor'
