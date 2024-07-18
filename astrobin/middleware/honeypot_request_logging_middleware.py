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
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        headers = {key: value for key, value in request.META.items() if key.startswith('HTTP_')}
        body = request.body.decode('utf-8') if request.body else 'No body content'

        self.logger.info(
            f"""
                    Honeypot Request
                    IP Address: {ip}
                    Request Path: {request.path}
                    Request Method: {request.method}
                    User Agent: {user_agent}
                    Headers: {headers}
                    Body: {body}
                """
        )
