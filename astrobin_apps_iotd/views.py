# Python
from datetime import datetime, timedelta

# Django
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    ListView)
from django.views.generic.base import View

# Third party
from braces.views import (
    GroupRequiredMixin,
    JSONResponseMixin,
    LoginRequiredMixin)

# AstroBin
from astrobin.models import Image

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
        LoginRequiredMixin, GroupRequiredMixin, CreateView):
    group_required = 'iotd_submitters'
    form_class = IotdSubmissionCreateForm
    http_method_names = ['post']
    template_name = 'astrobin_apps_iotd/iotdsubmission_create.html'

    def post(self, request, *args, **kwargs):
        image = Image.objects.get(pk = request.POST.get('image'))
        may, reason = may_submit_image(request.user, image)

        if may:
            try:
                submission = IotdSubmission.objects.create(
                    submitter = request.user,
                    image = image)
                messages.success(self.request, _("Image successfully submitted to the IOTD Submissions Queue"))
            except ValidationError as e:
                messages.error(self.request, ';'.join(e.messages))
        else:
            messages.error(request, reason)

        return redirect(reverse_lazy('image_detail', args = (image.pk,)))


class IotdSubmissionDetailView(
        LoginRequiredMixin, GroupRequiredMixin, DetailView,
        RestrictToSubmissionSubmitterOrSuperiorMixin):
    model = IotdSubmission
    group_required = [
        'iotd_submitters', 'iotd_reviewers', 'iotd_judges']


class IotdSubmissionQueueView(
        LoginRequiredMixin, GroupRequiredMixin, ListView):
    group_required = ['iotd_reviewers']
    model = IotdSubmission
    template_name = 'astrobin_apps_iotd/iotdsubmission_queue.html'

    def get_queryset(self):
        weeks = settings.IOTD_SUBMISSION_WINDOW_WEEKS
        cutoff = datetime.now() - timedelta(weeks = weeks)
        return list(set([x.image for x in self.model.objects.filter(date__gte = cutoff)]))


class IotdToggleVoteAjaxView(
        JSONResponseMixin, LoginRequiredMixin, GroupRequiredMixin, View):
    group_required = 'iotd_reviewers'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            image = get_object_or_404(Image, pk = kwargs.get('pk'))
            try:
                vote, created = IotdVote.objects.get_or_create(
                    reviewer = request.user,
                    image = image)
                if not created:
                    vote.delete()
                return self.render_json_response({
                    'vote': vote.pk,
                    'toggled': created,
                    'error': None,
                })
            except ValidationError as e:
                return self.render_json_response({
                    'vote': None,
                    'toggled': False,
                    'error': ';'.join(e.messages),
                })

        return HttpResponseForbidden()
