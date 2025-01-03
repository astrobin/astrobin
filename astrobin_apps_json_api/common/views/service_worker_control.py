import logging

from braces.views import JSONResponseMixin
from django.views.generic.base import View
from rest_framework.authtoken.models import Token

log = logging.getLogger(__name__)


class ServiceWorkerControl(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs):
        if 'HTTP_AUTHORIZATION' in request.META:
            token_in_header = request.META['HTTP_AUTHORIZATION'].replace('Token ', '')
            try:
                token = Token.objects.get(key=token_in_header)
                user = token.user
            except Token.DoesNotExist:
                user = None
        else:
            user = request.user

        return self.render_json_response(
            {
                'swEnabled': user is not None and user.is_superuser
            }
        )
