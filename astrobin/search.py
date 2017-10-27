from haystack.generic_views import SearchView
from haystack.query import SearchQuerySet, SQ

from django.shortcuts import render_to_response
from django.conf import settings
from django.utils.translation import ugettext as _

from forms import AdvancedSearchForm
from views import jsonDump, valueReader
from models import Telescope, Camera

import operator
import unicodedata

class AstroBinSearchView(SearchView):
    form_class = AdvancedSearchForm

    def get_queryset(self):
        q = self.request.GET.get('q')
        try:
            q = unicodedata.normalize('NFKD', q).encode('ascii', 'ignore')
        except:
            pass

        self.query = q
        sqs = super(AstroBinSearchView, self).get_queryset()

        ssms = self.request.GET.get('ssms')
        if ssms:
            sqs = sqs.filter(solar_system_main_subject = ssms)

        search_type = self.request.GET.get('type')
        if search_type:
            sqs = sqs.filter(**{search_type: q})

        if 'sort' in self.request.GET:
            order_by = self.request.GET['sort']
            sqs = sqs.order_by(order_by)

        return sqs
