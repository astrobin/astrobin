# Django
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views.generic import (
    base,
    CreateView,
    DetailView,
    ListView,
    UpdateView,
)

# This app
from rawdata.forms import (
    PrivateSharedFolderForm,
    PrivateSharedFolder_ImagesForm,
    PrivateSharedFolder_SelectExistingForm,
)
from rawdata.mixins import RestrictToSubscriberMixin
from rawdata.models import PrivateSharedFolder, RawImage
from rawdata.zip import *

# Other AstroBin apps
from common.mixins import AjaxableResponseMixin


class RestrictToInviteeMixin(object):
    def dispatch(self, request, *args, **kwargs):
        folder = get_object_or_404(PrivateSharedFolder, pk = kwargs.get('pk'))
        user = request.user

        if user != folder.creator and user not in folder.users.all():
            raise Http404

        return super(RestrictToInviteeMixin, self).dispatch(request, *args, **kwargs)


class PrivateSharedFolderCreateView(RestrictToSubscriberMixin, AjaxableResponseMixin, CreateView):
    model = PrivateSharedFolder
    form_class = PrivateSharedFolderForm

    def get_context_data(self, **kwargs):
        context = super(PrivateSharedFolderCreateView, self).get_context_data(**kwargs)
        images = RawImage.objects.by_ids_or_params(self.kwargs.pop('ids', ''), self.request.GET)
        if not images:
            raise Http404

        context['images'] = images
        if PrivateSharedFolder.objects.all():
            context['folders_form'] = PrivateSharedFolder_SelectExistingForm()

        return context
 
    def form_valid(self, form):
        folder = form.save(commit = False)
        folder.creator = self.request.user
        folder.save()

        return super(PrivateSharedFolderCreateView, self).form_valid(form)


class PrivateSharedFolderAddDataView(RestrictToSubscriberMixin, RestrictToInviteeMixin,
                                     AjaxableResponseMixin, UpdateView):
    model = PrivateSharedFolder
    form_class = PrivateSharedFolder_ImagesForm

    def form_valid(self, form):
        folder = form.save(commit = False)
        new = form.cleaned_data['images']
        for image in new:
            folder.images.add(image)
        folder.save()
        return super(PrivateSharedFolderAddDataView, self).form_valid(form)


class PrivateSharedFolderAddImageView(RestrictToSubscriberMixin, RestrictToInviteeMixin, base.View):
    def post(self, request, *args, **kwargs):
        folder = get_object_or_404(PrivateSharedFolder, pk = kwargs.get('pk'))
        image = get_object_or_404(Image, pk = request.POST.get('image'))
        folder.processed_images.add(image)
        messages.success(request, _("Your image has been added to the private shared folder."))

        response_kwargs = {'content_type': 'application/json'}
        return HttpResponse({}, **response_kwargs)


class PrivateSharedFolderDetailView(RestrictToSubscriberMixin, RestrictToInviteeMixin, DetailView):
    model = PrivateSharedFolder

    def get_context_data(self, **kwargs):
        context = super(PrivateSharedFolderDetailView, self).get_context_data(**kwargs)
        content_type = ContentType.objects.get_for_model(self.model)

        context['size'] = sum(x.size for x in self.get_object().images.all())
        context['content_type'] = ContentType.objects.get_for_model(self.model)
        return context


class PrivateSharedFolderDownloadView(RestrictToSubscriberMixin, RestrictToInviteeMixin, base.View):
    def get(self, request, *args, **kwargs):
        folder = get_object_or_404(PrivateSharedFolder, pk = kwargs.pop('pk'))
        if folder.archive:
            return HttpResponseRedirect(
                reverse('rawdata.temporary_archive_detail',
                        args=(folder.archive.pk,)))

        response, archive = serve_zip(folder.images.all(), self.request.user)
        folder.archive = archive
        folder.save()

        return response


class PrivateSharedFolderListView(RestrictToSubscriberMixin, ListView):
    model = PrivateSharedFolder

    def get_queryset(self):
        return self.model.objects.filter(
            Q(creator = self.request.user) |
            Q(users = self.request.user))

