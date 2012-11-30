# Python
from operator import itemgetter
import simplejson

# Django
from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.functional import lazy 
from django.utils.translation import ugettext as _
from django.views.generic import *
from django.views.generic.edit import BaseDeleteView

# This app
from .folders import *
from .forms import *
from .mixins import AjaxableResponseMixin, RestrictToSubscriberMixin
from .models import *
from .utils import *
from .zip import serve_zip

class RawImageCreateView(RestrictToSubscriberMixin, CreateView):
    model = RawImage
    form_class = RawImageUploadForm
    # success_url = lazy(reverse, str)('/') # TODO: url to user's raw data
    success_url = '/'

    def form_valid(self, form):
        raw_image = form.save(commit = False)
        raw_image.user = self.request.user
        raw_image.size = form.cleaned_data['file']._size
        raw_image.save(index = True)

        return super(RawImageCreateView, self).form_valid(form)


class RawImageDownloadView(RestrictToSubscriberMixin, base.View):
    def get(self, request, *args, **kwargs):
        images = RawImage.objects.by_ids_or_params(kwargs.pop('ids', ''), self.request.GET)
        if not images:
            raise Http404

        if len(images) == 1:
            image = images[0]

            if not image.active:
                raise Http404

            wrapper = FixedFileWrapper(file(image.file.path))
            response = HttpResponse(wrapper, content_type = 'application/octet-stream')
            response['Content-Disposition'] = 'attachment; filename=%s' % image.original_filename
            response['Content-Length'] = image.size
            return response

        response, archive = serve_zip(images, self.request.user)
        return response


class RawImageDeleteView(RestrictToSubscriberMixin, BaseDeleteView):
    def get_object(self):
        # We either delete my many ids or some query params
        return None

    def delete(self, request, *args, **kwargs):
        ids = kwargs.pop('ids', '')
        images = RawImage.objects.by_ids_or_params(ids, self.request.GET)
        images.delete()

        if request.is_ajax():
            context = {}
            context['success'] = True
            if ids:
                context['ids'] = ','.join(ids)
            return HttpResponse(
                simplejson.dumps(context),
                mimetype = 'application/json')

        return HttpResponseRedirect(self.get_success_url())


class RawImageLibrary(RestrictToSubscriberMixin, TemplateView):
    template_name = 'rawdata/library.html'

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

        context['filter_type'] = self.request.GET.get('type')
        context['filter_upload'] = self.request.GET.get('upload')

        all_images = RawImage.objects.filter(user = self.request.user)

        f = self.request.GET.get('f', 'upload')
        if not f or f == 'none':
            factory = FOLDER_TYPE_LOOKUP['none'](source = all_images)
            context['images'] = factory.filter(self.request.GET)
        else:
            try:
                factory = FOLDER_TYPE_LOOKUP[f](source = all_images)
                factory.filter(self.request.GET)

                context['folders_header'] = factory.get_label()
                context['folders'] = factory.produce()
            except KeyError:
                raise Http404

        return context


class TemporaryArchiveDetailView(RestrictToSubscriberMixin, DetailView):
    model = TemporaryArchive


class PublicDataPoolCreateView(RestrictToSubscriberMixin, AjaxableResponseMixin, CreateView):
    model = PublicDataPool
    form_class = PublicDataPoolForm

    def get_context_data(self, **kwargs):
        context = super(PublicDataPoolCreateView, self).get_context_data(**kwargs)
        images = RawImage.objects.by_ids_or_params(self.kwargs.pop('ids', ''), self.request.GET)
        if not images:
            raise Http404

        context['images'] = images
        if PublicDataPool.objects.all():
            context['pools_form'] = PublicDataPool_SelectExistingForm()

        return context
 
    def form_valid(self, form):
        pool = form.save(commit = False)
        pool.creator = self.request.user
        pool.save()

        return super(PublicDataPoolCreateView, self).form_valid(form)


class PublicDataPoolAddDataView(RestrictToSubscriberMixin, AjaxableResponseMixin, UpdateView):
    model = PublicDataPool
    form_class = PublicDataPool_ImagesForm

    def form_valid(self, form):
        pool = form.save(commit = False)
        new = form.cleaned_data['images']
        for image in new:
            pool.images.add(image)
        pool.save()
        return super(PublicDataPoolAddDataView, self).form_valid(form)


class PublicDataPoolDetailView(DetailView):
    model = PublicDataPool

    def get_context_data(self, **kwargs):
        context = super(PublicDataPoolDetailView, self).get_context_data(**kwargs)
        context['size'] = sum(x.size for x in self.get_object().images.all())
        return context


class PublicDataPoolDownloadView(RestrictToSubscriberMixin, base.View):
    def get(self, request, *args, **kwargs):
        pool = get_object_or_404(PublicDataPool, pk = kwargs.pop('pk'))
        if pool.archive:
            return HttpResponseRedirect(
                reverse('rawdata.temporary_archive_detail',
                        args=(pool.archive.pk,)))

        response, archive = serve_zip(pool.images.all(), self.request.user)
        pool.archive = archive
        pool.save()

        return response


class Help1(TemplateView):
    template_name = 'rawdata/help_01.html'

class Help2(TemplateView):
    template_name = 'rawdata/help_02.html'

class Help3(TemplateView):
    template_name = 'rawdata/help_03.html'

