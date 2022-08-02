import os

import boto3
from elasticsearch import RequestsHttpConnection
from requests_aws4auth import AWS4Auth

HAYSTACK_DEFAULT_OPERATOR = 'AND'
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 60

if os.environ.get('ELASTICSEARCH_URL'):
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
            'URL': os.environ.get('ELASTICSEARCH_URL').strip(),
            'INDEX_NAME': 'astrobin',
            'EXCLUDED_INDEXES': [
                'threaded_messages.search_indexes.Thread',
                'threaded_messages.search_indexes.ThreadIndex',
            ]
        },
    }

    if 'es.amazonaws.com' in HAYSTACK_CONNECTIONS['default']['URL']:
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 'us-east-1', 'es',
                           session_token=credentials.token)

        HAYSTACK_CONNECTIONS['default']['KWARGS'] = {
            'port': 443,
            'http_auth': awsauth,
            'use_ssl': True,
            'verify_certs': True,
            'connection_class': RequestsHttpConnection,
        }
    else:
        HAYSTACK_CONNECTIONS['default']['KWARGS'] = {
            'port': 9200,
            'use_ssl': False,
            'verify_certs': False,
        }
else:
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
            'INDEX_NAME': 'astrobin',
            'EXCLUDED_INDEXES': [
                'threaded_messages.search_indexes.Thread',
                'threaded_messages.search_indexes.ThreadIndex',
            ]
        },
    }

if not TESTING:
    HAYSTACK_SIGNAL_PROCESSOR = 'celery_haystack.signals.CelerySignalProcessor'
else:
    HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.BaseSignalProcessor'
