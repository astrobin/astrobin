import os

from elasticsearch import RequestsHttpConnection
from requests_aws4auth import AWS4Auth


class AWS4AuthEncodingFix(AWS4Auth):
    def __call__(self, request):
        request = super(AWS4AuthEncodingFix, self).__call__(request)

        for header_name in request.headers:
            self._encode_header_to_utf8(request, header_name)

        return request

    def _encode_header_to_utf8(self, request, header_name):
        value = request.headers[header_name]

        if isinstance(value, unicode):
            value = value.encode('utf-8')

        if isinstance(header_name, unicode):
            del request.headers[header_name]
            header_name = header_name.encode('utf-8')

        request.headers[header_name] = value


HAYSTACK_DEFAULT_OPERATOR = 'AND'
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 70

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': os.environ.get('ELASTICSEARCH_URL', 'http://elasticsearch').strip(),
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
        'http_auth': AWS4AuthEncodingFix(
            os.environ.get('AWS_ACCESS_KEY_ID').strip(),
            os.environ.get('AWS_SECRET_ACCESS_KEY').strip(),
            os.environ.get('ELASTIC_SEARCH_AWS_REGION', 'us-east-1').strip(),
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
