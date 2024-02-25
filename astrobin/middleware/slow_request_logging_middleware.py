import logging
import time


class SlowRequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger(__name__)
        self.threshold = 2  # Time in seconds

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        end_time = time.time()

        duration = end_time - start_time
        if duration > self.threshold:
            self.logger.warning(f'Slow request: {request.path} took {duration:.2f}s')

        return response
