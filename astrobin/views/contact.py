from django.views.generic import RedirectView

from common.services import AppRedirectionService


class ContactRedirectView(RedirectView):
    permanent = False
    query_string = True
    pattern_name = 'contact'

    def get_redirect_url(self, *args, **kwargs):
        return AppRedirectionService.contact_redirect(self.request)
