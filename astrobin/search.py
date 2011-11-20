from haystack.views import SearchView

class ImageSearchView(SearchView):
    def __name__(self):
        return 'ImageSearchView'

    def get_results(self):
        sqs = super(ImageSearchView, self).get_results()
        if 'sort' in self.request.GET:
            order_by = self.request.GET['sort']
            sqs = sqs.order_by(order_by)

        return sqs
