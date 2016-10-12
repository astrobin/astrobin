# Django
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView)
from django.views.generic.base import View

# Third party
from braces.views import (
    GroupRequiredMixin,
    JSONResponseMixin,
    LoginRequiredMixin)

# This app
from astrobin_apps_iotd.forms import *
from astrobin_apps_iotd.models import *
from astrobin_apps_iotd.permissions import *


class RestrictToSubmissionSubmitterOrSuperiorMixin(View):
    def dispatch(self, request, *args, **kwargs):
        submission = get_object_or_404(IotdSubmission, pk = kwargs['pk'])
        if not (
                request.user == submission.submitter or
                request.user.groups.filter(name = 'iotd_reviewers').exists() or
                request.user.groups.filter(name = 'iotd_judges').exists()):
            return HttpResponseForbidden()
        return super(RestrictToSubmissionSubmitterOrSuperiorMixin, self).dispatch(request, *args, **kwargs)


class IotdSubmissionCreateView(
        JSONResponseMixin, LoginRequiredMixin,
        GroupRequiredMixin, CreateView):
    group_required = 'iotd_submitters'
    form_class = IotdSubmissionCreateForm
    http_method_names = ['post']
    template_name = 'astrobin_apps_iotd/iotdsubmission_create.html'

    def post(self, request, *args, **kwargs):
        image = Image.objects.get(pk = request.POST.get('image'))
        may, reason = may_submit_image(request.user, image)

        if may:
            submission = IotdSubmission.objects.create(
                submitter = request.user,
                image = image)
            messages.success(self.request, _("Image successfully submitted to the IOTD Submissions Queue"))
        else:
            messages.error(request, _("You cannot submit your own image."))

        return redirect(reverse_lazy('image_detail', args = (image.pk,)))


class IotdSubmissionDetailView(
        LoginRequiredMixin, GroupRequiredMixin, DetailView,
        RestrictToSubmissionSubmitterOrSuperiorMixin):
    model = IotdSubmission
    group_required = [
        'iotd_submitters', 'iotd_reviewers', 'iotd_judges']
