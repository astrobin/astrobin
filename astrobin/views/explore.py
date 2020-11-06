from django.views.generic import ListView

from astrobin.models import Image
from astrobin_apps_iotd.services import IotdService


class TopPicksView(ListView):
    model = Image
    template_name = 'top_picks.html'
    paginate_by = 30

    def filter_by_datasource(self, queryset):
        data_source = self.request.GET.get("source")
        if data_source is not None:
            data_source = data_source.upper().replace('-', '_')
            if data_source in Image.DATA_SOURCE_TYPES:
                queryset = queryset.filter(data_source=data_source)

        return queryset

    def filter_by_acquisition_type(self, queryset):
        acquisition_type = self.request.GET.get("acquisition_type")
        if acquisition_type is not None:
            acquisition_type = acquisition_type.upper().replace('-', '_')
            if acquisition_type in Image.ACQUISITION_TYPES:
                queryset = queryset.filter(acquisition_type=acquisition_type)

        return queryset

    def get_queryset(self):
        queryset = IotdService().get_top_picks()
        queryset = self.filter_by_datasource(queryset)
        queryset = self.filter_by_acquisition_type(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(TopPicksView, self).get_context_data(**kwargs)
        context['source'] = self.request.GET.get('source')
        context['acquisition_type'] = self.request.GET.get('acquisition_type')
        return context


class TopPickNominationsView(TopPicksView):
    template_name = 'top_pick_nominations.html'

    def get_queryset(self):
        queryset = IotdService().get_top_pick_nominations()
        queryset = self.filter_by_datasource(queryset)
        queryset = self.filter_by_acquisition_type(queryset)
        return queryset
