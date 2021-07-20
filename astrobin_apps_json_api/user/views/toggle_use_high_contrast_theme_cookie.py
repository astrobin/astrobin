from datetime import datetime, timedelta

from braces.views import JsonRequestResponseMixin
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from common.services import AppRedirectionService


@method_decorator(csrf_exempt, name='dispatch')
class ToggleUseHighContrastThemeCookie(JsonRequestResponseMixin, View):
    def post(self, request, *args, **kwargs):
        cookie_name = "astrobin_use_high_contrast_theme"
        response = self.render_json_response({"status": "OK"})

        if request.COOKIES.get(cookie_name):
            response.delete_cookie(cookie_name, domain=AppRedirectionService.cookie_domain(request))
        else:
            max_age = 365 * 10 * 24 * 60 * 60
            expires = datetime.strftime(datetime.utcnow() + timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
            response.set_cookie(
                cookie_name, 1, max_age=max_age, expires=expires, domain=AppRedirectionService.cookie_domain(request))

        return response
