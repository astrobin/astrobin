from two_factor.views import LoginView as BaseLoginView


class LoginView(BaseLoginView):
    success_url_allowed_hosts = {'localhost:4400', 'app.astrobin.com'}
    redirect_authenticated_user = True

    def get_redirect_url(self):
        url = super().get_redirect_url()

        if '/account/login' in url:
            return ''

        return url
