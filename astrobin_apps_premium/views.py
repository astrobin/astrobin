# Django
from django.conf import settings
from django.views.generic import TemplateView

# Third party
from subscription.models import Subscription


class CancelView(TemplateView):
    template_name = 'astrobin_apps_premium/cancel.html'

class SuccessView(TemplateView):
    template_name = 'astrobin_apps_premium/success.html'

class EditView(TemplateView):
    template_name = 'astrobin_apps_premium/edit.html'

    def get_context_data(self, **kwargs):
        context = super(EditView, self).get_context_data(**kwargs)

        context['base_url'] = settings.ASTROBIN_BASE_URL
        context['business'] = settings.SUBSCRIPTION_PAYPAL_SETTINGS['business']

        return context
