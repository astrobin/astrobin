from datetime import timedelta, datetime

from braces.views import (
    GroupRequiredMixin,
    JSONResponseMixin,
    LoginRequiredMixin)
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.utils import formats
from django.utils.translation import ugettext
from django.views.generic import (
    ListView)
from django.views.generic.base import View

from astrobin.models import Image
from astrobin_apps_iotd.models import Iotd, IotdSubmission, IotdVote
from astrobin_apps_iotd.permissions import may_elect_iotd
from astrobin_apps_iotd.templatetags.astrobin_apps_iotd_tags import (
    iotd_submissions_today,
    iotd_votes_today,
    iotd_elections_today)
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_lite, is_premium, is_premium_2020, \
    is_ultimate_2020, is_lite_2020


class IotdBaseQueueView(View):
    def get_context_data(self, **kwargs):
        context = super(IotdBaseQueueView, self).get_context_data(**kwargs)
        context['MAX_SUBMISSIONS_PER_DAY'] = settings.IOTD_SUBMISSION_MAX_PER_DAY
        context['MAX_VOTES_PER_DAY'] = settings.IOTD_REVIEW_MAX_PER_DAY
        context['MAX_ELECTIONS_PER_DAY'] = settings.IOTD_JUDGEMENT_MAX_PER_DAY
        return context


class IotdSubmissionQueueView(
    LoginRequiredMixin, GroupRequiredMixin, IotdBaseQueueView, ListView):
    group_required = ['iotd_submitters']
    model = Image
    template_name = 'astrobin_apps_iotd/iotd_submission_queue.html'

    def get_queryset(self):
        days = settings.IOTD_SUBMISSION_WINDOW_DAYS
        judges = Group.objects.get(name='iotd_judges').user_set.all()
        image_groups = []

        def can_add(image):
            # type: (Image) -> bool

            # Since the introduction of the 2020 plans, Free and Lite users cannot participate in the IOTD/TP.
            # Older subscriptions (Lite/Premium) are still allowed, to offer continuity.
            user_has_rights = is_lite(image.user) or \
                              is_premium(image.user) or \
                              is_lite_2020(image.user) or \
                              is_premium_2020(image.user) or \
                              is_ultimate_2020(image.user)  # type: bool

            already_iotd = Iotd.objects.filter(image=x, date__lte=datetime.now().date()).exists()  # type: bool
            user_is_judge = x.user in judges  # type: bool

            return not user_has_rights and not (already_iotd or user_is_judge)

        for date in (datetime.now().date() - timedelta(n) for n in range(days)):
            image_groups.append({
                'date': date,
                'images': sorted(list(set([
                    x
                    for x in self.model.objects \
                        .filter(
                        moderator_decision=1,
                        published__gte=date,
                        published__lt=date + timedelta(1))
                    if can_add(x)])), key=lambda x: x.published, reverse=True)})

        return image_groups


class IotdToggleSubmissionAjaxView(
    JSONResponseMixin, LoginRequiredMixin, GroupRequiredMixin, View):
    group_required = 'iotd_submitters'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            image = Image.objects.get(pk=kwargs.get('pk'))
            try:
                submission, created = IotdSubmission.objects.get_or_create(
                    submitter=request.user,
                    image=image)
                if not created:
                    submission.delete()
                    return self.render_json_response({
                        'used_today': iotd_submissions_today(request.user),
                    })
                else:
                    return self.render_json_response({
                        'submission': submission.pk,
                        'used_today': iotd_submissions_today(request.user),
                    })
            except ValidationError as e:
                return self.render_json_response({
                    'error': ';'.join(e.messages),
                })

        return HttpResponseForbidden()


class IotdReviewQueueView(
    LoginRequiredMixin, GroupRequiredMixin, IotdBaseQueueView, ListView):
    group_required = ['iotd_reviewers']
    model = IotdSubmission
    template_name = 'astrobin_apps_iotd/iotd_review_queue.html'

    def get_queryset(self):
        days = settings.IOTD_REVIEW_WINDOW_DAYS
        cutoff = datetime.now() - timedelta(days)
        judges = Group.objects.get(name='iotd_judges').user_set.all()
        return sorted(list(set([
            x.image
            for x in self.model.objects.filter(date__gte=cutoff)
            if not Iotd.objects.filter(
                image=x.image,
                date__lte=datetime.now().date()).exists()
               and not x.image.user in judges])), key=lambda x: x.published, reverse=True)


class IotdToggleVoteAjaxView(
    JSONResponseMixin, LoginRequiredMixin, GroupRequiredMixin, View):
    group_required = 'iotd_reviewers'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            image = get_object_or_404(Image, pk=kwargs.get('pk'))
            try:
                vote, created = IotdVote.objects.get_or_create(
                    reviewer=request.user,
                    image=image)
                if not created:
                    vote.delete()
                    return self.render_json_response({
                        'used_today': iotd_votes_today(request.user),
                    })
                else:
                    return self.render_json_response({
                        'vote': vote.pk,
                        'used_today': iotd_votes_today(request.user),
                    })
            except ValidationError as e:
                return self.render_json_response({
                    'error': ';'.join(e.messages),
                })

        return HttpResponseForbidden()


class IotdJudgementQueueView(
    LoginRequiredMixin, GroupRequiredMixin, IotdBaseQueueView, ListView):
    group_required = ['iotd_judges']
    model = IotdVote
    template_name = 'astrobin_apps_iotd/iotd_judgement_queue.html'

    def get_queryset(self):
        days = settings.IOTD_JUDGEMENT_WINDOW_DAYS
        cutoff = datetime.now() - timedelta(days)
        judges = Group.objects.get(name='iotd_judges').user_set.all()
        return sorted(list(set([
            x.image
            for x in self.model.objects.filter(date__gte=cutoff)
            if not Iotd.objects.filter(
                image=x.image,
                date__lte=datetime.now().date()).exists()
               and not x.image.user in judges])), key=lambda x: x.published, reverse=True)


class IotdToggleJudgementAjaxView(
    JSONResponseMixin, LoginRequiredMixin, GroupRequiredMixin, View):
    group_required = 'iotd_judges'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            image = get_object_or_404(Image, pk=kwargs.get('pk'))
            ret = None

            try:
                # Only delete it if it's in the future and from the same
                # judge.
                iotd = Iotd.objects.get(image=image)
                if iotd.date <= datetime.now().date():
                    ret = {
                        'iotd': iotd.pk,
                        'date': formats.date_format(iotd.date, "SHORT_DATE_FORMAT"),
                        'used_today': iotd_elections_today(request.user),
                        'error': ugettext("You cannot unelect a past or current IOTD."),
                    }
                elif iotd.judge != request.user:
                    ret = {
                        'iotd': iotd.pk,
                        'date': formats.date_format(iotd.date, "SHORT_DATE_FORMAT"),
                        'used_today': iotd_elections_today(request.user),
                        'error': ugettext("You cannot unelect an IOTD elected by another judge."),
                    }
                else:
                    iotd.delete()
                    ret = {
                        'used_today': iotd_elections_today(request.user),
                    }
            except Iotd.DoesNotExist:
                max_days = settings.IOTD_JUDGEMENT_MAX_FUTURE_DAYS
                for date in (datetime.now().date() + timedelta(n) for n in range(max_days)):
                    try:
                        iotd = Iotd.objects.get(date=date)
                    except Iotd.DoesNotExist:
                        may, reason = may_elect_iotd(request.user, image)
                        if may:
                            iotd = Iotd.objects.create(
                                judge=request.user,
                                image=image,
                                date=date)
                            ret = {
                                'iotd': iotd.pk,
                                'date': formats.date_format(iotd.date, "SHORT_DATE_FORMAT"),
                                'used_today': iotd_elections_today(request.user),
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
    queryset = Iotd.objects\
        .filter(date__lte=datetime.now().date(), image__deleted=None)\
        .exclude(image__corrupted=True)
    template_name = 'astrobin_apps_iotd/iotd_archive.html'
    paginate_by = 30


class IotdSubmittersForImageAjaxView(
    LoginRequiredMixin, GroupRequiredMixin, View):
    group_required = 'iotd_reviewers'

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            image = get_object_or_404(Image, pk=kwargs['pk'])
            submitters = [x.submitter for x in IotdSubmission.objects.filter(image=image)]

            return render(request, 'astrobin_apps_users/inclusion_tags/user_list.html', {
                'view': 'table',
                'layout': 'compact',
                'user_list': submitters,
            })

        return HttpResponseForbidden()


class IotdReviewersForImageAjaxView(
    LoginRequiredMixin, GroupRequiredMixin, View):
    group_required = 'iotd_judges'

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            image = get_object_or_404(Image, pk=kwargs['pk'])
            reviewers = [x.reviewer for x in IotdVote.objects.filter(image=image)]

            return render(request, 'astrobin_apps_users/inclusion_tags/user_list.html', {
                'view': 'table',
                'layout': 'compact',
                'user_list': reviewers,
            })

        return HttpResponseForbidden()
