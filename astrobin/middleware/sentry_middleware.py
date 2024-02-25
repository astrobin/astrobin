from django.conf import settings
from sentry_sdk import set_user


class SentryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.SENTRY_DNS:
            if request.user.is_authenticated:
                set_user({"id": request.user.id})
            else:
                set_user(None)

        response = self.get_response(request)
        return response

