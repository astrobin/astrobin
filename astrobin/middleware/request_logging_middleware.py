import logging

from astrobin.utils import get_client_ip


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('http_requests')

    def __call__(self, request):
        response = self.get_response(request)
        self.log_request(request)
        return response

    def log_request(self, request):
        ip = get_client_ip(request)
        self.logger.debug(f"Request from {ip}: {request.method} {request.get_full_path()}")
