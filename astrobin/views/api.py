# Django
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

# Third party
from braces.views import LoginRequiredMixin

# AstroBin
from astrobin.forms import AppApiKeyRequestForm
from astrobin.models import AppApiKeyRequest


class AppApiKeyRequestView(LoginRequiredMixin, FormView):
    template_name = 'app_api_key_request.html'
    form_class = AppApiKeyRequestForm
    success_url = reverse_lazy('app_api_key_request_complete')

    def form_valid(self, form):
        key_request = AppApiKeyRequest(registrar = self.request.user)
        form = self.form_class(data = self.request.POST, instance = key_request)
        form.save()
        return super(AppApiKeyRequestView, self).form_valid(form)


class AppApiKeyRequestCompleteView(LoginRequiredMixin, TemplateView):
    template_name = 'app_api_key_request_complete.html'
