from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.http import last_modified
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import ListView

from astrobin.models import Image
from astrobin_apps_iotd.models import TopPickArchive
from astrobin_apps_iotd.services import IotdService
from common.services.caching_service import CachingService


class TopPickBaseView(ListView):
    def filter_by_datasource(self, queryset):
        data_source = self.request.GET.get("source")
        if data_source is not None:
            data_source = data_source.upper().replace('-', '_')
            if data_source in Image.DATA_SOURCE_TYPES:
                queryset = queryset.filter(image__data_source=data_source)

        return queryset

    def filter_by_acquisition_type(self, queryset):
        acquisition_type = self.request.GET.get("acquisition_type")
        if acquisition_type is not None:
            acquisition_type = acquisition_type.upper().replace('-', '_')
            if acquisition_type in Image.ACQUISITION_TYPES:
                queryset = queryset.filter(image__acquisition_type=acquisition_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(TopPickBaseView, self).get_context_data(**kwargs)
        context['source'] = self.request.GET.get('source')
        context['acquisition_type'] = self.request.GET.get('acquisition_type')
        return context


@method_decorator([
    last_modified(CachingService.get_latest_top_pick_datetime),
    cache_control(private=True, no_cache=True),
    vary_on_cookie
], name='dispatch')
class TopPicksView(TopPickBaseView):
    model = TopPickArchive
    template_name = 'top_picks.html'
    paginate_by = 30

    def get_queryset(self):
        queryset = IotdService().get_top_picks()
        queryset = self.filter_by_datasource(queryset)
        queryset = self.filter_by_acquisition_type(queryset)
        return queryset


@method_decorator([
    last_modified(CachingService.get_latest_top_pick_nomination_datetime),
    cache_control(private=True, no_cache=True),
    vary_on_cookie
], name='dispatch')
class TopPickNominationsView(TopPickBaseView):
    template_name = 'top_pick_nominations.html'
    model = TopPickArchive

    def get_queryset(self):
        queryset = IotdService().get_top_pick_nominations()
        queryset = self.filter_by_datasource(queryset)
        queryset = self.filter_by_acquisition_type(queryset)
        return queryset
