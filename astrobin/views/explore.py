# Python
from datetime import datetime

# Django
from django.db.models import Q
from django.views.generic import ListView

# Third party
from haystack.query import SearchQuerySet

# AstroBin
from astrobin.models import Image

# Other AstroBin apps
from astrobin_apps_iotd.models import Iotd, IotdVote


class WallView(ListView):
    template_name = 'wall.html'
    paginate_by = 70
    sorting_map = {
        '-uploaded': '-uploaded',
        '-acquired': '-last_acquisition_date',
        '-views': '-views',
        '-likes': '-likes',
        '-bookmarks': '-bookmarks',
        '-integration': '-integration',
        '-comments': '-comments',
    }

    def get_queryset(self):
        sqs = SearchQuerySet().all().models(Image)

        filter = self.request.GET.get('filter')
        if filter == 'all_ds':
            sqs = sqs.filter(is_deep_sky = True)
        elif filter == 'all_ss':
            sqs = sqs.filter(is_solar_system = True)
        elif filter == 'sun':
            sqs = sqs.filter(is_sun = True)
        elif filter == 'moon':
            sqs = sqs.filter(is_moon = True)
        elif filter == 'planets':
            sqs = sqs.filter(is_planets = True)
        elif filter == 'comets':
            sqs = sqs.filter(is_comets = True)
        elif filter == 'wide':
            sqs = sqs.filter(subject_type = 300)
        elif filter == 'trails':
            sqs = sqs.filter(subject_type = 400)
        elif filter == 'northernlights':
            sqs = sqs.filter(subject_type = 450)
        elif filter == 'gear':
            sqs = sqs.filter(subject_type = 500)
        elif filter == 'products':
            sqs = sqs.filter(is_commercial = True)
        elif filter == 'other':
            sqs = sqs.filter(subject_type = 600)

        data_source = self.request.GET.get("source")
        if data_source is not None:
            data_source = data_source.upper().replace('-', '_')
            if data_source in Image.DATA_SOURCE_TYPES:
                sqs = sqs.filter(data_source=data_source)

        try:
            sort = self.request.GET.get('sort')
            sqs = sqs.order_by(self.sorting_map[sort])
        except KeyError:
            sqs = sqs.order_by('-uploaded')

        return sqs

    def get_context_data(self, **kwargs):
        context = super(WallView, self).get_context_data(**kwargs)

        context['filter'] = self.request.GET.get('filter')
        context['sort'] = self.request.GET.get('sort')
        context['source'] = self.request.GET.get('source')

        if context['sort'] is None:
            context['sort'] = '-uploaded'

        return context


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
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super(TopPicksView, self).get_context_data(**kwargs)
        context['source'] = self.request.GET.get('source')
        return context
