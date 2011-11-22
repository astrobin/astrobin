from haystack.views import SearchView

from search_indexes import xapian_escape

class ImageSearchView(SearchView):
    def __name__(self):
        return 'ImageSearchView'

    def get_results(self):
        sqs = super(ImageSearchView, self).get_results()

        search_type = self.request.GET.get('type')
        q = xapian_escape(self.request.GET.get('q')).replace(' ', '')

        if search_type:
            sqs = sqs.filter(**{search_type: q})

        if 'sort' in self.request.GET:
            order_by = self.request.GET['sort']
            sqs = sqs.order_by(order_by)

        return sqs
