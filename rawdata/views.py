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
            raw_image.save()

        return super(RawImageCreateView, self).form_valid(form)
