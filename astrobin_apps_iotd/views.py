# Django
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
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
from astrobin_apps_iotd.models import IotdSubmission


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
    model = IotdSubmission
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseForbidden()

        return super(IotdSubmissionCreateView, self).post(
            request, *args, **kwargs)


class IotdSubmissionDetailView(
        LoginRequiredMixin, GroupRequiredMixin, DetailView,
        RestrictToSubmissionSubmitterOrSuperiorMixin):
    model = IotdSubmission
    group_required = [
        'iotd_submitters', 'iotd_reviewers', 'iotd_judges']
