# Django
from django.core.urlresolvers import reverse
from django.utils.functional import lazy 
from django.views.generic import *

# This app
from .models import RawImage
from .forms import RawImageUploadForm

class RawImageCreateView(CreateView):
    model = RawImage
    form_class = RawImageUploadForm
    template_name = 'rawimage/form.html'
    # success_url = lazy(reverse, str)('/') # TODO: url to user's raw data
    success_url = '/'

    def form_valid(self, form):
        if form.is_valid():
            raw_image = form.save(commit = False)
            raw_image.user = self.request.user
            raw_image.size = form.cleaned_data['file']._size
            raw_image.save()

        return super(RawImageCreateView, self).form_valid(form)


class RawImageLibrary(TemplateView):
    template_name = 'rawimage/library.html'    

    def get_used_bytes(self):
        sizes = RawImage.objects\
            .filter(user = self.request.user)\
            .values_list('size', flat = True)
        return sum(sizes)

    def get_used_percent(self, b): 
        return b * 100 / (1024*1024*1024*100)

    def get_progress_class(self, p):
        if p < 90: return 'progress-success'
        if p > 97: return 'progress-error'
        return 'progress-danger'

    def get_context_data(self, **kwargs):
        data = {}
        data['used_bytes'] = self.get_used_bytes()
        data['used_percent'] = self.get_used_percent(data['used_bytes'])
        data['progress_class'] = self.get_progress_class(data['used_percent'])

        return data
