from django.contrib.auth.views import LoginView as BaseLoginView


class LoginView(BaseLoginView):
    success_url_allowed_hosts = {'localhost:4400', 'app.astrobin.com'}
