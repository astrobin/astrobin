# Python
from datetime import datetime, timedelta

# Django
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext
from django.utils import formats
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
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


class IotdSubmissionQueueView(
        LoginRequiredMixin, GroupRequiredMixin, ListView):
    group_required = ['iotd_submitters']
    model = Image
    template_name = 'astrobin_apps_iotd/iotd_submission_queue.html'

    def get_queryset(self):
        weeks = settings.IOTD_SUBMISSION_WINDOW_WEEKS
        cutoff = datetime.now() - timedelta(weeks = weeks)
        return list(set([
            x
            for x in self.model.objects.filter(uploaded__gte = cutoff)
            if not Iotd.objects.filter(
                image = x,
                date__lte = datetime.now().date()).exists()]))


class IotdToggleSubmissionAjaxView(
        JSONResponseMixin, LoginRequiredMixin, GroupRequiredMixin, View):
    group_required = 'iotd_submitters'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            image = Image.objects.get(pk = kwargs.get('pk'))
            try:
                submission, created = IotdSubmission.objects.get_or_create(
                    submitter = request.user,
                    image = image)
                if not created:
                    submission.delete()
                    return self.render_json_response([])
                else:
                    return self.render_json_response({
                        'submission': submission.pk,
                    })
            except ValidationError as e:
                return self.render_json_response({
                    'error': ';'.join(e.messages),
                })

        return HttpResponseForbidden()


class IotdReviewQueueView(
        LoginRequiredMixin, GroupRequiredMixin, ListView):
    group_required = ['iotd_reviewers']
    model = IotdSubmission
    template_name = 'astrobin_apps_iotd/iotd_review_queue.html'

    def get_queryset(self):
        weeks = settings.IOTD_REVIEW_WINDOW_WEEKS
        cutoff = datetime.now() - timedelta(weeks = weeks)
        return list(set([
            x.image
            for x in self.model.objects.filter(date__gte = cutoff)
            if not Iotd.objects.filter(
                image = x.image,
                date__lte = datetime.now().date()).exists()]))


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
                    return self.render_json_response([])
                else:
                    return self.render_json_response({
                        'vote': vote.pk,
                    })
            except ValidationError as e:
                return self.render_json_response({
                    'error': ';'.join(e.messages),
                })

        return HttpResponseForbidden()


class IotdJudgementQueueView(
        LoginRequiredMixin, GroupRequiredMixin, ListView):
    group_required = ['iotd_judges']
    model = IotdVote
    template_name = 'astrobin_apps_iotd/iotd_judgement_queue.html'

    def get_queryset(self):
        weeks = settings.IOTD_JUDGEMENT_WINDOW_WEEKS
        cutoff = datetime.now() - timedelta(weeks = weeks)
        return list(set([
            x.image
            for x in self.model.objects.filter(date__gte = cutoff)
            if not Iotd.objects.filter(
                image = x.image,
                date__lte = datetime.now().date()).exists()]))


class IotdToggleJudgementAjaxView(
        JSONResponseMixin, LoginRequiredMixin, GroupRequiredMixin, View):
    group_required = 'iotd_judges'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            image = get_object_or_404(Image, pk = kwargs.get('pk'))
            ret = None

            try:
                # Only delete it if it's in the future and from the same
                # judge.
                iotd = Iotd.objects.get(image = image)
                if iotd.date <= datetime.now().date():
                    ret = {
                        'iotd': iotd.pk,
                        'date': formats.date_format(iotd.date, "SHORT_DATE_FORMAT"),
                        'error': ugettext("You cannot unelect a past or current IOTD."),
                    }
                elif iotd.judge != request.user:
                    ret = {
                        'iotd': iotd.pk,
                        'date': formats.date_format(iotd.date, "SHORT_DATE_FORMAT"),
                        'error': ugettext("You cannot unelect an IOTD elected by another judge."),
                    }
                else:
                    iotd.delete()
                    ret = {}
            except Iotd.DoesNotExist:
                max_days = settings.IOTD_JUDGMENT_MAX_FUTURE_DAYS
                for date in (datetime.now().date() + timedelta(n) for n in range(max_days)):
                    try:
                        iotd = Iotd.objects.get(date = date)
                    except Iotd.DoesNotExist:
                        may, reason = may_elect_iotd(request.user, image)
                        if may:
                            iotd = Iotd.objects.create(
                                judge = request.user,
                                image = image,
                                date = date)
                            ret = {
                                'iotd': iotd.pk,
                                'date': formats.date_format(iotd.date, "SHORT_DATE_FORMAT"),
                            }
                        else:
                            ret = {
                                'error': reason,
                            }

                        break
                if not ret:
                    ret = {
                        'error': ugettext("All IOTD slots for the next %(days)s days are already filled.") % {
                            'days': max_days,
                        },
                    }
            return self.render_json_response(ret)

        return HttpResponseForbidden()


class IotdArchiveView(ListView):
    model = Iotd
    queryset = Iotd.objects.filter(date__lte = datetime.now().date())
    template_name = 'astrobin_apps_iotd/iotd_archive.html'
    paginate_by = 30 


class IotdSubmittersForImageAjaxView(
        LoginRequiredMixin, GroupRequiredMixin, View):
    group_required = 'iotd_reviewers'

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            image = get_object_or_404(Image, pk = kwargs['pk'])
            submitters = [x.submitter for x in IotdSubmission.objects.filter(image = image)]

            return render_to_response(
                'astrobin_apps_users/inclusion_tags/user_list.html',
                {
                    'view': 'table',
                    'layout': 'compact',
                    'user_list': submitters,
                }, context_instance = RequestContext(request))

        return HttpResponseForbidden()


class IotdReviewersForImageAjaxView(
        LoginRequiredMixin, GroupRequiredMixin, View):
    group_required = 'iotd_judges'

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            image = get_object_or_404(Image, pk = kwargs['pk'])
            reviewers = [x.reviewer for x in IotdVote.objects.filter(image = image)]

            return render_to_response(
                'astrobin_apps_users/inclusion_tags/user_list.html',
                {
                    'view': 'table',
                    'layout': 'compact',
                    'user_list': reviewers,
                }, context_instance = RequestContext(request))

        return HttpResponseForbidden()
