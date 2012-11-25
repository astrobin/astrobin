# Python
import tempfile, zipfile

# Django
from django.contrib.auth.decorators import user_passes_test
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse
from django.utils.functional import lazy 
from django.views.generic import *
from django.utils.decorators import method_decorator

# This app
from .models import RawImage
from .folders import *
from .forms import RawImageUploadForm
from .utils import *

class RawImageCreateView(CreateView):
    model = RawImage
    form_class = RawImageUploadForm
    template_name = 'rawimage/form.html'
    # success_url = lazy(reverse, str)('/') # TODO: url to user's raw data
    success_url = '/'

    @method_decorator(user_passes_test(lambda u: user_has_active_subscription(u)))
    def dispatch(self, *args, **kwargs):
        return super(RawImageCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        if form.is_valid():
            raw_image = form.save(commit = False)
            raw_image.user = self.request.user
            raw_image.size = form.cleaned_data['file']._size
            raw_image.save(index = True)

        return super(RawImageCreateView, self).form_valid(form)


class RawImageDownloadView(base.View):
    def get(self, request, *args, **kwargs):
        # https://code.djangoproject.com/ticket/6027
        class FixedFileWrapper(FileWrapper):
            def __iter__(self):
                self.filelike.seek(0)
                return self

        ids = kwargs.pop('ids', '').split(',')
        if len(ids) == 1:
            try:
                image = RawImage.objects.get(id = ids[0])
            except RawImage.DoesNotExist:
                raise Http404

            if not image.active:
                raise Http404

            wrapper = FixedFileWrapper(file(image.file.path))
            response = HttpResponse(wrapper, content_type = 'application/octet-stream')
            response['Content-Disposition'] = 'attachment; filename=%s' % image.original_filename
            response['Content-Length'] = image.size
        else:
            temp = tempfile.TemporaryFile()
            archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
            for id in ids:
                try:
                    image = RawImage.objects.get(id = id)
                    archive.write(image.file.path, image.original_filename)
                except RawImage.DoesNotExist:
                    pass

            archive.close()
            wrapper = FixedFileWrapper(temp)
            response = HttpResponse(wrapper, content_type='application/zip')
            response['Content-Disposition'] = 'attachment; filename=rawdata.zip'
            response['Content-Length'] = temp.tell()
            temp.seek(0)

        return response


class RawImageLibrary(TemplateView):
    template_name = 'rawimage/library.html'    

    @method_decorator(user_passes_test(lambda u: user_has_active_subscription(u)))
    def dispatch(self, *args, **kwargs):
        return super(RawImageLibrary, self).dispatch(*args, **kwargs)

    def get_folders_by_type(self, user):
        images = RawImage.objects.filter(user = user, indexed = True)
        folders = {}
        for t in RawImage.TYPE_CHOICES:
            f = TypeFolder(type = t[0], label = t[1], source = images)
            f.populate()
            folders[f.get_type()] = {
                'label': f.get_label(),
                'images': f.get_images(),
            }
        
        return folders

    def get_context_data(self, **kwargs):
        total_files = RawImage.objects.filter(user = self.request.user)

        context = super(RawImageLibrary, self).get_context_data(**kwargs)
        context['byte_limit'] = user_byte_limit(self.request.user)
        context['used_bytes'] = user_used_bytes(self.request.user)
        context['used_percent'] = user_used_percent(self.request.user)
        context['over_limit'] = user_is_over_limit(self.request.user)
        context['progress_class'] = user_progress_class(self.request.user)
        context['total_files'] = total_files.count()
        context['unindexed_count'] = total_files.filter(indexed = False).count()

        folders = self.request.GET.get('f', None)
        if folders:
            pass
        else:
            context['images'] = RawImage.objects.filter(user = self.request.user)

        return context


class Help1(TemplateView):
    template_name = 'rawdata/help_01.html'

class Help2(TemplateView):
    template_name = 'rawdata/help_02.html'

class Help3(TemplateView):
    template_name = 'rawdata/help_03.html'

