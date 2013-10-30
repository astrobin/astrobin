# Django
from django.views.generic import TemplateView

class CancelView(TemplateView):
    template_name = 'astrobin_apps_donations/cancel.html'

class SuccessView(TemplateView):
    template_name = 'astrobin_apps_donations/success.html'

