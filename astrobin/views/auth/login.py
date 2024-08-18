from two_factor.forms import AuthenticationTokenForm, BackupTokenForm
from two_factor.views import LoginView as BaseLoginView

from astrobin.auth import CustomAuthenticationForm
from astrobin_apps_premium.services.premium_service import PremiumService
from common.services import AppRedirectionService


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

    def done(self, form_list, **kwargs):
        response = super().done(form_list, **kwargs)

        # If this is paying user, set a cookie to store this information. This can be used to bypass security checks
        # from AWS WAF.
        valid_usersubscription = PremiumService(self.request.user).get_valid_usersubscription()
        if valid_usersubscription:
            response.set_cookie(
                'astrobin_paying_user',
                '1',
                max_age=60 * 60 * 24 * 30,
                domain=AppRedirectionService.cookie_domain(self.request)
            )

        return response
