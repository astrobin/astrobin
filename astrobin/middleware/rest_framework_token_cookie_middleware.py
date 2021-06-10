from rest_framework.authtoken.models import Token

from common.services import AppRedirectionService

REST_FRAMEWORK_TOKEN_COOKIE = 'classic-auth-token'


class RestFrameworkTokenCookieMiddleware(object):
    def _process(self, request):
        return (
                hasattr(request, 'user') and
                request.user.is_authenticated() and
                not request.is_ajax() and
                not 'HTTP_AUTHORIZATION' in request.META and
                not request.COOKIES.get(REST_FRAMEWORK_TOKEN_COOKIE)
        )

    def process_response(self, request, response):
        if self._process(request):
            token, created = Token.objects.get_or_create(user=request.user)

            response.set_cookie(
                REST_FRAMEWORK_TOKEN_COOKIE,
                token,
                max_age=60 * 60 * 24 * 180,
                domain=AppRedirectionService.cookie_domain(request))

        return response
