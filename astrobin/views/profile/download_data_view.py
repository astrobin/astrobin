from datetime import datetime, timedelta

from braces.views import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView

from astrobin.forms.download_data_form import DownloadDataForm
from astrobin.models import DataDownloadRequest
from astrobin.tasks import prepare_download_data_archive
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import can_download_data


class DownloadDataView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    form_class = DownloadDataForm
    template_name = "user/profile/edit/download_data.html"
    success_url = reverse_lazy("profile_download_data")

    def test_func(self, user):
        return can_download_data(user)

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super(DownloadDataView, self).form_valid(form)

        messages.success(
            self.request,
            _("AstroBin is preparing your data for download. Please check this page again in a while: the more images "
              "you have, the more time it will take."))
        prepare_download_data_archive.apply_async(queue="default", args=(self.object.id,))

        return response

    def get_context_data(self, **kwargs):
        context = super(DownloadDataView, self).get_context_data(**kwargs)

        context.update({
            "exceeded_requests_quota": DataDownloadRequest.objects.filter(
                user=self.request.user,
                created__gte=datetime.now() - timedelta(days=1)
            ).count() > 0
        })

        return context
