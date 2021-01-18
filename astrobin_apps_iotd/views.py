import logging
from datetime import timedelta, datetime

from braces.views import (
    GroupRequiredMixin,
    JSONResponseMixin,
    LoginRequiredMixin)
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.utils import formats
from django.utils.translation import ugettext
from django.views.generic import (
    ListView)
from django.views.generic.base import View

from astrobin.models import Image
from astrobin_apps_iotd.models import Iotd, IotdVote
from astrobin_apps_iotd.permissions import may_elect_iotd
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_iotd.templatetags.astrobin_apps_iotd_tags import iotd_elections_today
from common.services import AppRedirectionService

log = logging.getLogger('apps')


class IotdBaseQueueView(View):
    def get_context_data(self, **kwargs):
        context = super(IotdBaseQueueView, self).get_context_data(**kwargs)
        context['MAX_ELECTIONS_PER_DAY'] = settings.IOTD_JUDGEMENT_MAX_PER_DAY
        return context


class IotdSubmissionQueueView(View):
    def dispatch(self, request, *args, **kwargs):
        return HttpResponsePermanentRedirect(AppRedirectionService.redirect(request, '/iotd/submission-queue'))


class IotdReviewQueueView(View):
    def dispatch(self, request, *args, **kwargs):
        return HttpResponsePermanentRedirect(AppRedirectionService.redirect(request, '/iotd/review-queue'))


class IotdJudgementQueueView(
    LoginRequiredMixin, GroupRequiredMixin, IotdBaseQueueView, ListView):
    group_required = ['iotd_judges']
    model = IotdVote
    template_name = 'astrobin_apps_iotd/iotd_judgement_queue.html'

    def get_queryset(self):
        return IotdService.get_judgement_queue()


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
                    log.info("User %d deleted IOTD for image %s" % (request.user.pk, image.get_id()))
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
                            log.info("User %d added IOTD for image %s" % (request.user.pk, image.get_id()))
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
    template_name = 'astrobin_apps_iotd/iotd_archive.html'
    paginate_by = 30

    def get_queryset(self):
        return IotdService().get_iotds()
