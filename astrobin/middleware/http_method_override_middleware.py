import logging


logger = logging.getLogger(__name__)

METHOD_OVERRIDE_HEADER = 'HTTP_X_HTTP_METHOD_OVERRIDE'

class HttpMethodOverrideMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST' and METHOD_OVERRIDE_HEADER in request.META:
            logger.debug(f"Overriding POST method with {request.META[METHOD_OVERRIDE_HEADER]} for {request.path}")
            request.method = request.META[METHOD_OVERRIDE_HEADER]

        return self.get_response(request)
