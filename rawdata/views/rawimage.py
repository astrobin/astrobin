import json

from django.contrib.contenttypes.models import ContentType
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.views.generic import (
    base,
    DetailView,
    TemplateView,
)
from django.views.generic.edit import BaseDeleteView
from rest_framework import generics
from rest_framework import permissions
from toggleproperties.models import ToggleProperty

from astrobin.models import Image
from rawdata.folders import FOLDER_TYPE_LOOKUP
from rawdata.mixins import RestrictToSubscriberMixin
from rawdata.models import RawImage
from rawdata.permissions import IsOwnerOrReadOnly, IsSubscriber
from rawdata.serializers import RawImageSerializer
from rawdata.utils import rawdata_user_used_bytes, rawdata_user_byte_limit, rawdata_user_used_percent, \
    rawdata_user_is_over_limit, rawdata_user_progress_class
from rawdata.zip import serve_zip


class RawImageDetailView(RestrictToSubscriberMixin, DetailView):
    model = RawImage

    def dispatch(self, *args, **kwargs):
        response = super(RawImageDetailView, self).dispatch(*args, **kwargs)
        if self.get_object().user != self.request.user:
            raise Http404

        return response


class RawImageDownloadView(RestrictToSubscriberMixin, base.View):
    def get(self, request, *args, **kwargs):
        images = RawImage.objects.by_ids_or_params(kwargs.pop('ids', ''), self.request.GET)
        if not images:
            raise Http404

        response = serve_zip(images, self.request.user)
        return response


class RawImageDeleteView(RestrictToSubscriberMixin, BaseDeleteView):
    # Dummy success_url, we don't actually need it, because we always request
    # this view via ajax.
    success_url = '/'

    def get_object(self):
        # We either delete my many ids or some query params
        return None

    def delete(self, request, *args, **kwargs):
        ids = kwargs.pop('ids', '')
        images = RawImage.objects.by_ids_or_params(ids, self.request.GET)

        for image in images:
            if image.user != request.user:
                raise Http404

        images.delete()

        if request.is_ajax():
            context = {}
            context['success'] = True
            if ids:
                context['ids'] = ','.join(ids)
            return HttpResponse(
                json.dumps(context),
                content_type='application/json')

        return HttpResponseRedirect(self.get_success_url())


class RawImageLibrary(RestrictToSubscriberMixin, TemplateView):
    template_name = 'rawdata/library.html'

    def get_folders_by_type(self, user):
        images = RawImage.objects.filter(user=user, indexed=True)
        folders = {}
        for t in RawImage.TYPE_CHOICES:
            f = TypeFolder(type=t[0], label=t[1], source=images)
            f.populate()
            folders[f.get_type()] = {
                'label': f.get_label(),
                'images': f.get_images(),
            }

        return folders

    def get_context_data(self, **kwargs):
        image_ct = ContentType.objects.get_for_model(Image)

        total_files = RawImage.objects.filter(user=self.request.user)

        context = super(RawImageLibrary, self).get_context_data(**kwargs)
        context['byte_limit'] = rawdata_user_byte_limit(self.request.user)
        context['used_bytes'] = rawdata_user_used_bytes(self.request.user)
        context['used_percent'] = rawdata_user_used_percent(self.request.user)
        context['over_limit'] = rawdata_user_is_over_limit(self.request.user)
        context['progress_class'] = rawdata_user_progress_class(self.request.user)
        context['total_files'] = total_files.count()
        context['unindexed_count'] = total_files.filter(indexed=False).count()
        context['requested_user'] = self.request.user
        context['public_images_no'] = Image.objects.filter(user=self.request.user).count()
        context['wip_images_no'] = Image.wip.filter(user=self.request.user).count()
        context['bookmarks_no'] = ToggleProperty.objects.toggleproperties_for_user("bookmark", self.request.user) \
            .filter(content_type=image_ct).count()
        context['likes_no'] = ToggleProperty.objects.toggleproperties_for_user("like", self.request.user) \
            .filter(content_type=image_ct).count()

        for filtering in (
                'type',
                'upload',
                'acquisition',
                'camera',
                'temperature',
        ):
            context['filter_' + filtering] = self.request.GET.get(filtering)

        all_images = RawImage.objects.filter(user=self.request.user)

        f = self.request.GET.get('f', 'upload')
        if not f or f == 'none':
            factory = FOLDER_TYPE_LOOKUP['none'](source=all_images)
            context['images'] = factory.filter(self.request.GET)
        else:
            try:
                factory = FOLDER_TYPE_LOOKUP[f](source=all_images)
                factory.filter(self.request.GET)

                context['folders_header'] = factory.get_label()
                context['folders'] = factory.produce()
            except KeyError:
                raise Http404

        return context


###############################################################################
# API                                                                         #
###############################################################################


class RawImageList(generics.ListCreateAPIView):
    model = RawImage
    serializer_class = RawImageSerializer
    permission_classes = (permissions.IsAuthenticated,
                          IsOwnerOrReadOnly,
                          IsSubscriber,)

    def get_queryset(self):
        return self.model.objects.order_by('pk')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RawImageDetail(generics.RetrieveUpdateDestroyAPIView):
    model = RawImage
    serializer_class = RawImageSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,
                          IsSubscriber)

    def get_queryset(self):
        return self.model.objects.order_by('pk')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
