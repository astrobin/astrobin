from braces.views import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView

from astrobin.forms.download_data_form import DownloadDataForm
from astrobin.tasks import prepare_download_data_archive


class DownloadDataView(LoginRequiredMixin, CreateView):
    form_class = DownloadDataForm
    template_name = "user/profile/edit/download_data.html"
    success_url = reverse_lazy("profile_download_data")

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super(DownloadDataView, self).form_valid(form)

        messages.success(
            self.request,
            _("AstroBin is preparing your data for download. Please check this page again in a while: the more images"
              "you have, the more time it will take."))
        prepare_download_data_archive.apply(args=(self.object.id,))

        return response
