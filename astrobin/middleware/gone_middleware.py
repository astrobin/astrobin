from django.http import HttpResponse
from django.template import loader

from common.exceptions import Http410


class GoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, Http410):
            template = loader.get_template('410.html')
            return HttpResponse(template.render({}, request), status=410)
