from two_factor.forms import AuthenticationTokenForm, BackupTokenForm
from two_factor.views import LoginView as BaseLoginView

from astrobin.auth import CustomAuthenticationForm


class LoginView(BaseLoginView):
    success_url_allowed_hosts = {'localhost:4400', 'app.astrobin.com'}
    redirect_authenticated_user = True
    form_list = (
        ('auth', CustomAuthenticationForm),
        ('token', AuthenticationTokenForm),
        ('backup', BackupTokenForm),
    )

    def get_redirect_url(self) -> str:
        url = super().get_redirect_url()

        if '/account/login' in url:
            return ''

        return url
