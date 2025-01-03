import logging

from braces.views import JSONResponseMixin
from django.views.generic.base import View

log = logging.getLogger(__name__)


class ServiceWorkerControl(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs):
        return self.render_json_response(
            {
                'swEnabled': request.user.is_authenticated and request.user.is_superuser
            }
        )
