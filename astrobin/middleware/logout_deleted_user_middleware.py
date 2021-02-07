from django.contrib.auth import logout


class LogoutDeletedUserMiddleware(object):
    def _process(self, request):
        return (
                hasattr(request, 'user') and
                request.user.is_authenticated() and
                hasattr(request.user, 'userprofile') and
                request.user.userprofile is not None
        )

    def process_response(self, request, response):
        if self._process(request):
            logout(request)

        return response
