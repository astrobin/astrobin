from django.views.generic import DetailView

from astrobin.models import ImageOfTheDay
from astrobin.models import Image

class IotdDetailView(DetailView):
    model = ImageOfTheDay
    context_object_name = 'iotd'
    pk_url_kwarg = 'iotd_pk'

    def get_context_data(self, **kwargs):
        iotd = self.get_object()
        candidates = Image.objects.filter(image_of_the_day_candidate__date = iotd.date)
        context = super(IotdDetailView, self).get_context_data(**kwargs)
        context['image_list'] = candidates
        context['alias'] = 'gallery'
        return context

    def get_template_names(self):
        if self.request.is_ajax():
            return 'inclusion_tags/image_list_entries.html'
        return 'iotd_detail.html'
