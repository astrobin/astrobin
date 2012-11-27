# Python
from operator import itemgetter
import simplejson
import tempfile, zipfile


# Django
from django.contrib.auth.decorators import user_passes_test
from django.core.files import File
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.functional import lazy 
from django.views.generic import *
from django.views.generic.edit import BaseDeleteView
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _

# This app
from .models import RawImage, TemporaryArchive
from .folders import *
from .forms import RawImageUploadForm
from .utils import *

class RawImageCreateView(CreateView):
    model = RawImage
    form_class = RawImageUploadForm
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

            if image.user != request.user:
                raise Http404

            wrapper = FixedFileWrapper(file(image.file.path))
            response = HttpResponse(wrapper, content_type = 'application/octet-stream')
            response['Content-Disposition'] = 'attachment; filename=%s' % image.original_filename
            response['Content-Length'] = image.size
        else:
                temp = tempfile.NamedTemporaryFile()
                archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
                for id in ids:
                    try:
                        image = RawImage.objects.get(id = id)

                        if not image.active:
                            continue

                        if image.user != request.user:
                            raise Http404

                        archive.write(image.file.path, image.original_filename)
                    except RawImage.DoesNotExist:
                        continue

                archive.close()

                size = sum([x.file_size for x in archive.infolist()])
                if size < 16*1024*1024:
                    wrapper = FixedFileWrapper(temp)
                    response = HttpResponse(wrapper, content_type='application/zip')
                    response['Content-Disposition'] = 'attachment; filename=rawdata.zip'
                    response['Content-Length'] = temp.tell()
                    temp.seek(0)
                else:
                    t = TemporaryArchive(
                        user = self.request.user,
                        size = size,
                    )
                    t.file.save('', File(temp))
                    t.save()
                    response = HttpResponseRedirect(
                        reverse('rawdata.temporary_archive_detail', args = (t.pk,)))

                temp.close()

        return response


class RawImageDeleteView(BaseDeleteView):
    def get_queryset(self):
        return RawImage.objects.filter(user = self.request.user)

    def delete(self, request, *args, **kwargs):
        ids = kwargs.pop('ids', '').split(',')
        for id in ids:
            try:
                image = self.get_queryset().get(id = id)
                image.delete()
            except RawImage.DoesNotExist:
                continue

        if request.is_ajax():
            return HttpResponse(
                simplejson.dumps({
                    'success': True,
                    'ids': ','.join(ids),
                }),
                mimetype = 'application/json')

        return HttpResponseRedirect(self.get_success_url())


class RawImageLibrary(TemplateView):
    template_name = 'rawdata/library.html'

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

        images = RawImage.objects.filter(user = self.request.user)

        context['filter_type'] = self.request.GET.get('type')
        context['filter_upload'] = self.request.GET.get('upload')

        f = self.request.GET.get('f', 'upload')
        if not f or f == 'none':
            context['images'] = images
        else:
            factory = None
            if f == 'type':
                factory = TypeFolderFactory(images)
                context['folders_header'] = _("Type");
            elif f == 'upload':
                factory = UploadDateFolderFactory(images)
                context['folders_header'] = _("Upload date")

            if factory:
                factory.filter(self.request.GET)
                context['folders'] = factory.produce()

        return context


class TemporaryArchiveDetailView(DetailView):
    model = TemporaryArchive


class Help1(TemplateView):
    template_name = 'rawdata/help_01.html'

class Help2(TemplateView):
    template_name = 'rawdata/help_02.html'

class Help3(TemplateView):
    template_name = 'rawdata/help_03.html'

