import logging

from braces.views import JsonRequestResponseMixin
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext
from django.views.decorators.cache import cache_control, cache_page
from django.views.decorators.http import last_modified
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import ListView, base
from rest_framework.authtoken.models import Token

from astrobin.models import Image
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.models import (
    Iotd, IotdDismissedImage, IotdReviewerSeenImage, IotdSubmission, IotdSubmitterSeenImage,
    IotdVote,
)
from astrobin_apps_iotd.services import IotdService
from common.services import AppRedirectionService
from common.services.caching_service import CachingService

log = logging.getLogger(__name__)


@method_decorator(
    [
        cache_page(3600),
        last_modified(CachingService.get_latest_iotd_datetime),
        cache_control(private=True),
        vary_on_cookie
    ], name='dispatch'
)
class IotdArchiveView(ListView):
    model = Iotd
    template_name = 'astrobin_apps_iotd/iotd_archive.html'
    paginate_by = 30

    def get_queryset(self):
        return IotdService().get_iotds()

    def dispatch(self, request, *args, **kwargs):
        if (
                request.user.is_authenticated and
                request.user.userprofile.enable_new_gallery_experience
        ):
            return redirect(AppRedirectionService.redirect('/explore/iotd-tp-archive'))
        return super().dispatch(request, *args, **kwargs)



class ImageStats(JsonRequestResponseMixin, base.View):
    def get(self, request, *args, **kwargs):
        image_id = kwargs.pop('image_id')
        image = ImageService.get_object(image_id, Image.objects_including_wip)

        if image is None:
            return HttpResponseNotFound()

        user = request.user
        if not user.is_authenticated and 'HTTP_AUTHORIZATION' in request.META:
            token_in_header = request.META['HTTP_AUTHORIZATION'].replace('Token ', '')
            token = Token.objects.get(key=token_in_header)
            user = token.user

        if user != image.user and not user.is_superuser:
            return HttpResponseForbidden()

        submitter_views = IotdSubmitterSeenImage.objects.filter(image=image).count()
        total_submitters = image.designated_iotd_submitters.count()
        submitter_views_percentage = 0 if total_submitters == 0 else submitter_views / total_submitters * 100

        reviewer_views = IotdReviewerSeenImage.objects.filter(image=image).count()
        total_reviewers = image.designated_iotd_reviewers.count()
        reviewer_views_percentage = 0 if total_reviewers == 0 else reviewer_views / total_reviewers * 100

        data = {
            'submitter_views': submitter_views,
            'total_submitters': total_submitters,
            'submitter_views_percentage': f'{submitter_views_percentage:.2f}%',
            'submissions': IotdSubmission.objects.filter(image=image).count(),
            'reviewer_views': reviewer_views,
            'total_reviewers': total_reviewers,
            'reviewer_views_percentage': f'{reviewer_views_percentage:.2f}%',
            'votes': IotdVote.objects.filter(image=image).count(),
            'early_dismissal': gettext('Yes')
            if IotdDismissedImage.objects.filter(image=image).count() >= settings.IOTD_MAX_DISMISSALS
            else gettext('No'),
        }

        return self.render_json_response(data)
