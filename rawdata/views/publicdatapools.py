from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.generic import (
    base,
    CreateView,
    DetailView,
    ListView,
    UpdateView,
)

from astrobin.models import Image
from common.mixins import AjaxableResponseMixin
from rawdata.forms import (
    PublicDataPoolForm,
    PublicDataPool_ImagesForm,
    PublicDataPool_SelectExistingForm,
)
from rawdata.mixins import RestrictToSubscriberMixin, RestrictToCreatorMixin
from rawdata.models import PublicDataPool, RawImage
from rawdata.zip import serve_zip


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
        pool = form.save(commit=False)
        pool.creator = self.request.user
        pool.save()

        return super(PublicDataPoolCreateView, self).form_valid(form)


class PublicDataPoolUpdateView(RestrictToCreatorMixin, RestrictToSubscriberMixin,
                               AjaxableResponseMixin, UpdateView):
    model = PublicDataPool
    form_class = PublicDataPoolForm

    def form_valid(self, form):
        form.save();
        return super(PublicDataPoolUpdateView, self).form_valid(form)


class PublicDataPoolAddDataView(RestrictToSubscriberMixin, AjaxableResponseMixin, UpdateView):
    model = PublicDataPool
    form_class = PublicDataPool_ImagesForm

    def form_valid(self, form):
        pool = form.save(commit=False)
        images = form.cleaned_data['images']
        pool.images.add(*images)
        return super(PublicDataPoolAddDataView, self).form_valid(form)


class PublicDataPoolRemoveDataView(RestrictToSubscriberMixin, base.View):
    model = PublicDataPool

    def post(self, request, *args, **kwargs):
        pool = get_object_or_404(PublicDataPool, pk=kwargs.get('pk'))
        rawimage = get_object_or_404(RawImage, pk=kwargs.get('rawimage_pk'))

        if request.user != rawimage.user:
            raise Http404

        pool.images.remove(rawimage)

        response_kwargs = {'content_type': 'application/json'}
        return HttpResponse({}, **response_kwargs)


class PublicDataPoolAddImageView(base.View):
    def post(self, request, *args, **kwargs):
        pool = get_object_or_404(PublicDataPool, pk=kwargs.get('pk'))
        image = get_object_or_404(Image, pk=request.POST.get('image'))
        pool.processed_images.add(image)
        messages.success(request, _("Your image has been added to the pool."))

        response_kwargs = {'content_type': 'application/json'}
        return HttpResponse({}, **response_kwargs)


class PublicDataPoolDetailView(DetailView):
    model = PublicDataPool

    def get_context_data(self, **kwargs):
        context = super(PublicDataPoolDetailView, self).get_context_data(**kwargs)
        content_type = ContentType.objects.get_for_model(self.model)

        context['size'] = sum(x.size for x in self.get_object().images.all())
        context['content_type'] = ContentType.objects.get_for_model(self.model)
        context['update_form'] = PublicDataPoolForm(instance=self.get_object())
        return context


class PublicDataPoolDownloadView(RestrictToPremiumOrSubscriberMixin, base.View):
    def get(self, request, *args, **kwargs):
        pool = get_object_or_404(PublicDataPool, pk=kwargs.pop('pk'))
        response = serve_zip(pool.images.all(), self.request.user, pool)
        return response


class PublicDataPoolListView(ListView):
    model = PublicDataPool
