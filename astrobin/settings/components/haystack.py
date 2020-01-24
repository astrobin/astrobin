import os

HAYSTACK_DEFAULT_OPERATOR = 'AND'
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 70
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': os.environ.get('ELASTICSEARCH_URL', 'http://elasticsearch:9200'),
        'INDEX_NAME': 'astrobin',
        'EXCLUDED_INDEXES': [
            'threaded_messages.search_indexes.Thread',
            'threaded_messages.search_indexes.ThreadIndex',
        ],
    },
}

if not TESTING:
    HAYSTACK_SIGNAL_PROCESSOR = 'celery_haystack.signals.CelerySignalProcessor'

