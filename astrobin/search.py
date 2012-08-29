from haystack.views import SearchView
from haystack.query import SearchQuerySet, SQ

from django.shortcuts import render_to_response
from django.conf import settings
from django.utils.translation import ugettext as _

from views import jsonDump, valueReader
from models import Telescope, Camera
from templatetags.tags import gear_name

import operator
import unicodedata

class SearchView(SearchView):
    def __name__(self):
        return 'SearchView'

    def get_results(self):
        q = self.request.GET.get('q')
        try:
            q = unicodedata.normalize('NFKD', q).encode('ascii', 'ignore')
        except:
            pass

        self.query = q
        sqs = super(SearchView, self).get_results()

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

    def create_response(self):
        """
        Generates the actual HttpResponse to send back to the user.
        """
        (paginator, page) = self.build_page()
        
        strings = [
            "",
            _("No results. Sorry."),
            _("Matching items:"),
        ]

        context = {
            'query': self.query,
            'form': self.form,
            'page': page,
            'paginator': paginator,
            'suggestion': None,
        }
        
        if getattr(settings, 'HAYSTACK_INCLUDE_SPELLING', False):
            context['suggestion'] = self.form.get_suggestion()

        context.update(self.extra_context())
        return render_to_response(self.template, context, context_instance=self.context_class(self.request))

