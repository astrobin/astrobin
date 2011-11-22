from haystack.views import SearchView

from search_indexes import xapian_escape

class ImageSearchView(SearchView):
    def __name__(self):
        return 'ImageSearchView'

    def get_results(self):
        sqs = super(ImageSearchView, self).get_results()

        search_type = self.request.GET.get('type')
        q = xapian_escape(self.request.GET.get('q')).replace(' ', '')

        if search_type == 'imaging_telescopes':
            sqs = sqs.filter(imaging_telescopes = q)
        elif search_type == 'guiding_telescopes':
            sqs = sqs.filter(guiding_telescopes = q)
        elif search_type == 'mounts':
            sqs = sqs.filter(mounts = q)
        elif search_type == 'imaging_cameras':
            sqs = sqs.filter(imaging_cameras = q)
        elif search_type == 'guiding_cameras':
            sqs = sqs.filter(guiding_cameras = q)
        elif search_type == 'focal_reducers':
            sqs = sqs.filter(focal_reducers = q)
        elif search_type == 'software':
            sqs = sqs.filter(software = q)
        elif search_type == 'filters':
            sqs = sqs.filter(filters = q)
        elif search_type == 'accessories':
            sqs = sqs.filter(accessories = q)

        if 'sort' in self.request.GET:
            order_by = self.request.GET['sort']
            sqs = sqs.order_by(order_by)

        return sqs
