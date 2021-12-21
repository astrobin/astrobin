from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


class LogoutView(BaseLogoutView):
    success_url_allowed_hosts = {'localhost:4400', 'app.astrobin.com'}

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, args, kwargs)

        # noinspection PyBroadException
        try:
            domain = 'localhost' if 'localhost' in request.META.get('HTTP_REFERER') else '.astrobin.com'
        except:
            domain = '.astrobin.com'

        response.delete_cookie('classic-auth-token', '/', domain)

        return response
