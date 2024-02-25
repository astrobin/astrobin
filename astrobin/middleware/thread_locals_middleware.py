import threading


_thread_locals = threading.local()


def get_request_cache():
    if not hasattr(_thread_locals, 'request_cache'):
        _thread_locals.request_cache = {}
    return _thread_locals.request_cache


class ThreadLocalsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request_cache = {
            'user': getattr(request, 'user', None),
        }

        response = self.get_response(request)

        _thread_locals.request_cache = {}

        return response
