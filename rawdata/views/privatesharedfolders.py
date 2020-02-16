import json

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.generic import (
    base,
    edit,
    CreateView,
    DetailView,
    ListView,
    UpdateView,
)

from astrobin.models import Image, UserProfile
from common.mixins import AjaxableResponseMixin
# This app
from rawdata.forms import (
    PrivateSharedFolderForm,
    PrivateSharedFolder_ImagesForm,
    PrivateSharedFolder_SelectExistingForm,
    PrivateSharedFolder_UsersForm,
)
from rawdata.mixins import RestrictToSubscriberMixin, RestrictToCreatorMixin
from rawdata.models import PrivateSharedFolder, RawImage
from rawdata.zip import serve_zip


class RestrictToInviteeMixin(object):
    def dispatch(self, request, *args, **kwargs):
        folder = get_object_or_404(PrivateSharedFolder, pk=kwargs.get('pk'))
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
        if PrivateSharedFolder.objects.filter(Q(creator=self.request.user) | Q(users=self.request.user)):
            context['folders_form'] = PrivateSharedFolder_SelectExistingForm(user=self.request.user)

        return context

    def form_valid(self, form):
        folder = form.save(commit=False)
        folder.creator = self.request.user
        folder.save()

        return super(PrivateSharedFolderCreateView, self).form_valid(form)


class PrivateSharedFolderUpdateView(RestrictToCreatorMixin, RestrictToSubscriberMixin,
                                    AjaxableResponseMixin, UpdateView):
    model = PrivateSharedFolder
    form_class = PrivateSharedFolderForm

    def form_valid(self, form):
        form.save();
        return super(PrivateSharedFolderUpdateView, self).form_valid(form)


class PrivateSharedFolderAddDataView(RestrictToSubscriberMixin, RestrictToInviteeMixin,
                                     AjaxableResponseMixin, UpdateView):
    model = PrivateSharedFolder
    form_class = PrivateSharedFolder_ImagesForm

    def form_valid(self, form):
        folder = form.save(commit=False)
        images = form.cleaned_data['images']
        folder.images.add(*images)
        return super(PrivateSharedFolderAddDataView, self).form_valid(form)


class PrivateSharedFolderRemoveDataView(RestrictToSubscriberMixin, RestrictToInviteeMixin,
                                        base.View):
    model = PrivateSharedFolder

    def post(self, request, *args, **kwargs):
        folder = get_object_or_404(PrivateSharedFolder, pk=kwargs.get('pk'))
        rawimage = get_object_or_404(RawImage, pk=kwargs.get('rawimage_pk'))

        if request.user != rawimage.user:
            raise Http404

        folder.images.remove(rawimage)

        response_kwargs = {'content_type': 'application/json'}
        return HttpResponse({}, **response_kwargs)


class PrivateSharedFolderAddImageView(RestrictToInviteeMixin, base.View):
    def post(self, request, *args, **kwargs):
        folder = get_object_or_404(PrivateSharedFolder, pk=kwargs.get('pk'))
        image = get_object_or_404(Image, pk=request.POST.get('image'))
        folder.processed_images.add(image)
        messages.success(request, _("Your image has been added to the private shared folder."))

        response_kwargs = {'content_type': 'application/json'}
        return HttpResponse({}, **response_kwargs)


class PrivateSharedFolderAddUsersView(RestrictToSubscriberMixin, RestrictToInviteeMixin,
                                      AjaxableResponseMixin, UpdateView):
    model = PrivateSharedFolder
    form_class = PrivateSharedFolder_UsersForm

    def form_valid(self, form):
        folder = self.get_object()
        usernames = form.cleaned_data['users'].split(',')
        for username in usernames:
            try:
                user = UserProfile.objects.get(user__username=username).user
                folder.users.add(user)
            except UserProfile.DoesNotExist:
                print "User does not exist: %s" % username
                continue
        return super(PrivateSharedFolderAddUsersView, self).form_valid(form)


class PrivateSharedFolderRemoveUserView(RestrictToSubscriberMixin, RestrictToCreatorMixin,
                                        base.View):
    model = PrivateSharedFolder

    def post(self, request, *args, **kwargs):
        folder = get_object_or_404(PrivateSharedFolder, pk=kwargs.get('pk'))
        user = get_object_or_404(User, pk=kwargs.get('user_id'))
        folder.users.remove(user)

        response_kwargs = {'content_type': 'application/json'}
        return HttpResponse({}, **response_kwargs)


class PrivateSharedFolderDetailView(RestrictToInviteeMixin, DetailView):
    model = PrivateSharedFolder

    def get_context_data(self, **kwargs):
        context = super(PrivateSharedFolderDetailView, self).get_context_data(**kwargs)
        content_type = ContentType.objects.get_for_model(self.model)

        context['size'] = sum(x.size for x in self.get_object().images.all())
        context['content_type'] = ContentType.objects.get_for_model(self.model)
        context['update_form'] = PrivateSharedFolderForm(instance=self.get_object())
        context['users'] = self.get_object().users.all()
        context['users_form'] = PrivateSharedFolder_UsersForm()
        context['users_form_source'] = json.dumps(
            list(User.objects \
                 .exclude(pk=self.request.user.pk)
                 .exclude(privatesharedfolders_invited=self.get_object()) \
                 .values_list('username', flat=True)))
        return context


class PrivateSharedFolderDownloadView(RestrictToInviteeMixin, base.View):
    def get(self, request, *args, **kwargs):
        folder = get_object_or_404(PrivateSharedFolder, pk=kwargs.pop('pk'))
        response = serve_zip(folder.images.all(), self.request.user, folder)
        return response


class PrivateSharedFolderListView(ListView):
    model = PrivateSharedFolder

    def get_queryset(self):
        return self.model.objects.filter(
            Q(creator=self.request.user) |
            Q(users=self.request.user))


class PrivateSharedFolderDeleteView(RestrictToSubscriberMixin, RestrictToCreatorMixin,
                                    edit.BaseDeleteView):
    model = PrivateSharedFolder

    def get_queryset(self):
        return self.model.objects.filter(creator=self.request.user)

    def delete(Self, request, *args, **kwargs):
        folder = get_object_or_404(PrivateSharedFolder, pk=kwargs.pop('pk'))
        folder.delete();

        messages.success(request, _("Your private shared folder has been deleted."))

        response_kwargs = {'content_type': 'application/json'}
        return HttpResponse({}, **response_kwargs)
