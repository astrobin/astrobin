import logging

from braces.views import JsonRequestResponseMixin
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.utils.decorators import method_decorator
from django.utils.translation import gettext
from django.views.decorators.cache import cache_control, cache_page
from django.views.decorators.http import last_modified
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import ListView

from astrobin.models import Image
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.models import (
    Iotd, IotdDismissedImage, IotdReviewerSeenImage, IotdSubmission, IotdSubmitterSeenImage,
    IotdVote,
)
from astrobin_apps_iotd.services import IotdService
from common.services.caching_service import CachingService
from django.views.generic import base

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


class ImageStats(JsonRequestResponseMixin, base.View):
    def get(self, request, *args, **kwargs):
        image_id = kwargs.pop('image_id')
        image = ImageService.get_object(image_id, Image.objects_including_wip)

        if image is None:
            return HttpResponseNotFound()

        if request.user != image.user and not request.user.is_superuser:
            return HttpResponseForbidden()

        data = {
            'submitter_views': IotdSubmitterSeenImage.objects.filter(image=image).count(),
            'submissions': IotdSubmission.objects.filter(image=image).count(),
            'reviewer_views': IotdReviewerSeenImage.objects.filter(image=image).count(),
            'votes': IotdVote.objects.filter(image=image).count(),
            'early_dismissal': gettext('Yes')
            if IotdDismissedImage.objects.filter(image=image).count() >= 5
            else gettext('No'),
        }

        return self.render_json_response(data)
