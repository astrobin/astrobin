import logging

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control, cache_page
from django.views.decorators.http import last_modified
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import ListView

from astrobin_apps_iotd.models import Iotd
from astrobin_apps_iotd.services import IotdService
from common.services.caching_service import CachingService

log = logging.getLogger('apps')


@method_decorator([
    cache_page(3600),
    last_modified(CachingService.get_latest_iotd_datetime),
    cache_control(private=True),
    vary_on_cookie
], name='dispatch')
class IotdArchiveView(ListView):
    model = Iotd
    template_name = 'astrobin_apps_iotd/iotd_archive.html'
    paginate_by = 30

    def get_queryset(self):
        return IotdService().get_iotds()
