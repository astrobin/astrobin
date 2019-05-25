# Python
from datetime import datetime

# Django
from django.db.models import Q
from django.views.generic import ListView


# AstroBin
from astrobin.models import Image


class TopPicksView(ListView):
    model = Image
    template_name = 'top_picks.html'
    paginate_by = 30

    def get_queryset(self):
        queryset = self.model.objects.exclude(iotdvote = None).filter(
            Q(iotd = None) |
            Q(iotd__date__gt = datetime.now().date())).order_by('-published')

        data_source = self.request.GET.get("source")
        if data_source is not None:
            data_source = data_source.upper().replace('-', '_')
            if data_source in Image.DATA_SOURCE_TYPES:
                queryset = queryset.filter(data_source = data_source)

        acquisition_type = self.request.GET.get("acquisition_type")
        if acquisition_type is not None:
            acquisition_type = acquisition_type.upper().replace('-', '_')
            if acquisition_type in Image.ACQUISITION_TYPES:
                queryset = queryset.filter(acquisition_type=acquisition_type)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super(TopPicksView, self).get_context_data(**kwargs)
        context['source'] = self.request.GET.get('source')
        context['acquisition_type'] = self.request.GET.get('acquisition_type')
        return context
