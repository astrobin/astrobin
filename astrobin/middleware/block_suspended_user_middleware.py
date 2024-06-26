from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext

from astrobin.middleware.mixins import MiddlewareParentClass


class BlockSuspendedUserMiddleware(MiddlewareParentClass):
    def _process(self, request):
        if not hasattr(request, 'user'):
            return False

        if not hasattr(request.user, 'userprofile'):
            return False

        if '/suspended-account/' in request.path or '/contact/' in request.path:
            return False

        return request.user.userprofile.suspended is not None


    def process_response(self, request, response):
        if self._process(request):
            if 'HTTP_AUTHORIZATION' in request.META:
                return HttpResponseBadRequest(
                    gettext(
                        'Your account is temporarily or permanently suspended. If you believe this is in error, '
                        'please get in touch using the Help menu.'
                    )
                )

            return redirect(reverse('suspended_account') + '?requester')

        return response
