from haystack.views import SearchView
from haystack.query import SearchQuerySet, SQ

from django.shortcuts import render_to_response
from django.conf import settings
from django.utils.translation import ugettext as _

from search_indexes import xapian_escape
from views import jsonDump, valueReader
from models import Telescope, Camera

import operator
import unicodedata

class ImageSearchView(SearchView):
    def __name__(self):
        return 'ImageSearchView'

    def get_results(self):
        q = self.request.GET.get('q')
        if q:
            q = xapian_escape(q).replace(' ', '')
        try:
            q = unicodedata.normalize('NFKD', q).encode('ascii', 'ignore')
        except:
            pass

        self.query = q
        sqs = super(ImageSearchView, self).get_results()

        search_type = self.request.GET.get('type')
        if search_type:
            sqs = sqs.filter(**{search_type: q})

        for tag, klass in {'imaging_telescopes': Telescope,
                           'imaging_cameras': Camera}.iteritems():
            ids, value = valueReader(self.request.GET, tag)
            ks = []
            for id in ids:
                try:
                    id = int(id)
                    k = klass.objects.get(id=id)
                except ValueError:
                    k = klass.objects.filter(name=id)
                    if k:
                        k = k[0]
                if k:
                    ks.append(k)
                else:
                    # Nothing found? We can abort and return empty queryset.
                    return SearchQuerySet().none()

            if ks:
                filters = reduce(operator.or_, [SQ(**{tag: xapian_escape(k.name).replace(' ', '')}) for k in ks])
                sqs = sqs.filter(filters).exclude(**{tag: None})

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
            _("Enter partial name and wait for the suggestions!"),
            _("No results. Sorry."),
            _("Matching items:"),
        ]

        # Prepare prefills
        prefills = {}
        for tag, klass in {'imaging_telescopes': Telescope,
                           'imaging_cameras': Camera}.iteritems():
            ids, value = valueReader(self.request.GET, tag)
            prefills[tag] = []
            for id in ids:
                try:
                    id = int(id)
                    k = klass.objects.get(id=id)
                except ValueError:
                    k = klass.objects.filter(name=id)
                    if k:
                        k = k[0]
                if k:
                    prefills[tag].append(k)

        context = {
            'query': self.query,
            'form': self.form,
            'page': page,
            'paginator': paginator,
            'suggestion': None,
            'prefill_dict': {
                'imaging_telescopes': [jsonDump(prefills['imaging_telescopes'])] + strings,
                'imaging_cameras': [jsonDump(prefills['imaging_cameras'])] + strings,
             }
        }
        
        if getattr(settings, 'HAYSTACK_INCLUDE_SPELLING', False):
            context['suggestion'] = self.form.get_suggestion()

        context.update(self.extra_context())
        return render_to_response(self.template, context, context_instance=self.context_class(self.request))

