# Django
from django.http import Http404
from django.views.generic import (
    base,
    CreateView,
    TemplateView,
)
from django.views.generic.edit import BaseDeleteView


# This app
from rawdata.folders import *
from rawdata.forms import RawImageUploadForm
from rawdata.mixins import RestrictToSubscriberMixin
from rawdata.models import RawImage
from rawdata.utils import *
from rawdata.zip import *

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

        for filtering in (
            'type',
            'upload',
            'acquisition',
            'camera',
            'temperature',
        ):
            context['filter_' + filtering] = self.request.GET.get(filtering)

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

