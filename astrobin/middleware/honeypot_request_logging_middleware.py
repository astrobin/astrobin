import logging

from astrobin.utils import get_client_ip


class HoneypotRequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('http_requests')
        self.honeypot_username = 'honeypot'

    def __call__(self, request):
        response = self.get_response(request)
        if self.honeypot_username in request.path:
            self.log_request(request)
        return response

    def log_request(self, request):
        ip = get_client_ip(request)
        self.logger.debug(f"Honeypot request from {ip}: {request.method} {request.get_full_path()}")
