# Django
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.utils.functional import lazy 
from django.views.generic import *
from django.utils.decorators import method_decorator

# This app
from .models import RawImage
from .forms import RawImageUploadForm
from .groups import is_premium, byte_limit
from .utils import *

class RawImageCreateView(CreateView):
    model = RawImage
    form_class = RawImageUploadForm
    template_name = 'rawimage/form.html'
    # success_url = lazy(reverse, str)('/') # TODO: url to user's raw data
    success_url = '/'

    @method_decorator(user_passes_test(lambda u: is_premium(u)))
    def dispatch(self, *args, **kwargs):
        return super(RawImageCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        if form.is_valid():
            raw_image = form.save(commit = False)
            raw_image.user = self.request.user
            raw_image.size = form.cleaned_data['file']._size
            raw_image.save()

        return super(RawImageCreateView, self).form_valid(form)


class RawImageLibrary(TemplateView):
    template_name = 'rawimage/library.html'    

    @method_decorator(user_passes_test(lambda u: is_premium(u)))
    def dispatch(self, *args, **kwargs):
        return super(RawImageLibrary, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        total_files = RawImage.objects.filter(user = self.request.user)

        context = super(RawImageLibrary, self).get_context_data(**kwargs)
        context['byte_limit'] = byte_limit(self.request.user)
        context['used_bytes'] = user_used_bytes(self.request.user)
        context['used_percent'] = user_used_percent(self.request.user)
        context['over_limit'] = user_is_over_limit(self.request.user)
        context['progress_class'] = user_progress_class(self.request.user)
        context['total_files'] = total_files.count()
        context['unindexed_count'] = total_files.filter(indexed = False).count()

        return context


class Help1(TemplateView):
    template_name = 'rawdata/help_01.html'

class Help2(TemplateView):
    template_name = 'rawdata/help_02.html'

class Help3(TemplateView):
    template_name = 'rawdata/help_03.html'

