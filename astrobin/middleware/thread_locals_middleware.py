import threading
from typing import Optional

from django.contrib.auth.models import User

_thread_locals = threading.local()


def get_current_user() -> Optional[User]:
    return getattr(_thread_locals, 'user', None)


class ThreadLocalsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        return self.get_response(request)
