import logging

class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('http_requests')

    def __call__(self, request):
        response = self.get_response(request)
        self.log_request(request)
        return response

    def log_request(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        self.logger.debug(f"Request from {ip}: {request.method} {request.get_full_path()}")
