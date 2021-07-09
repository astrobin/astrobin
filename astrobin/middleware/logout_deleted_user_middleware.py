from django.contrib.auth import logout

from astrobin.middleware.mixins import MiddlewareParentClass


class LogoutDeletedUserMiddleware(MiddlewareParentClass):
    def _process(self, request):
        return (
                hasattr(request, 'user') and
                request.user.is_authenticated and
                hasattr(request.user, 'userprofile') and
                request.user.userprofile.deleted is not None
        )

    def process_response(self, request, response):
        if self._process(request):
            logout(request)

        return response
