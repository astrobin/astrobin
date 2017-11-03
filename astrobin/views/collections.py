# Django
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse_lazy
from django.db import IntegrityError
from django.forms import ValidationError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic.base import View

# AstroBin
from astrobin.forms import CollectionCreateForm
from astrobin.forms import CollectionUpdateForm
from astrobin.forms import CollectionAddRemoveImagesForm
from astrobin.models import Collection
from astrobin.models import Image

# Third party
from braces.views import LoginRequiredMixin
from braces.views import JSONResponseMixin


class EnsureCollectionOwnerMixin(View):
    def dispatch(self, request, *args, **kwargs):
        collection = get_object_or_404(Collection, pk = kwargs[self.pk_url_kwarg])
        if request.user != collection.user:
            return HttpResponseForbidden

        return super(EnsureCollectionOwnerMixin, self).dispatch(request, *args, **kwargs)


class RedirectToCollectionListMixin():
    def get_success_url(self):
        return reverse_lazy('user_collections_list', args = (self.kwargs['username'],))


class UserCollectionsBase(View):
    model = Collection

    def get_queryset(self):
        qs = super(UserCollectionsBase, self).get_queryset()
        return qs.filter(user__username = self.kwargs['username'])

    def get_context_data(self, **kwargs):
        context = super(UserCollectionsBase, self).get_context_data(**kwargs)
        context['requested_user'] = User.objects.get(username = self.kwargs['username'])

        # TODO: stats

        return context


class UserCollectionsList(UserCollectionsBase, ListView):
    template_name = 'user_collections_list.html'
    context_object_name = 'collections_list'

    def get_context_data(self, **kwargs):
        context = super(UserCollectionsList, self).get_context_data(**kwargs)
        context['non_empty_collections_count'] = self.get_queryset().exclude(images = None).count()
        context['view'] = self.request.GET.get('view')
        return context


class UserCollectionsBaseEdit(LoginRequiredMixin, UserCollectionsBase, View):
    def form_valid(self, form):
        collection = form.save(commit = False)
        collection.user = self.request.user
        try:
            return super(UserCollectionsBaseEdit, self).form_valid(form)
        except IntegrityError:
            from django.forms.util import ErrorList
            form._errors["name"] = ErrorList([_("You already have a collection with that name")])
            return self.form_invalid(form)


class UserCollectionsCreate(
        UserCollectionsBaseEdit, RedirectToCollectionListMixin, CreateView):
    form_class = CollectionCreateForm
    template_name = 'user_collections_create.html'


class UserCollectionsUpdate(
        RedirectToCollectionListMixin, EnsureCollectionOwnerMixin,
        UserCollectionsBaseEdit, UpdateView):
    form_class = CollectionUpdateForm
    template_name = 'user_collections_update.html'
    pk_url_kwarg = 'collection_pk'
    context_object_name = 'collection'

    def get_form(self, form_class):
        form = super(UserCollectionsUpdate, self).get_form(form_class)
        form.fields['cover'].queryset = Collection.objects.get(pk = self.kwargs['collection_pk']).images.all()
        return form

    def get_success_url(self):
        url = self.request.GET.get('next')
        if url:
            return url
        return super(UserCollectionsUpdate, self).get_success_url()

    def post(self, *args, **kwargs):
        messages.success(self.request, _("Collection updated!"))
        return super(UserCollectionsUpdate, self).post(*args, **kwargs)

class UserCollectionsAddRemoveImages(
        JSONResponseMixin, EnsureCollectionOwnerMixin, UserCollectionsBaseEdit,
        UpdateView):
    form_class = CollectionAddRemoveImagesForm
    template_name = 'user_collections_add_remove_images.html'
    pk_url_kwarg = 'collection_pk'
    context_object_name = 'collection'
    content_type = None

    def get_context_data(self, **kwargs):
        context = super(UserCollectionsAddRemoveImages, self).get_context_data(**kwargs)
        context['images'] = Image.objects.filter(user__username = self.kwargs['username'])
        context['images_pk_in_collection'] = [x.pk for x in self.get_object().images.all()]
        return context

    def get_success_url(self):
        return reverse_lazy('user_collections_detail', args = (self.kwargs['username'], self.kwargs['collection_pk'],))

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            self.get_object().images.clear()
            for pk in request.POST.getlist('images[]'):
                image = Image.objects.get(pk = pk)
                self.get_object().images.add(image)

            messages.success(request, _("Collection updated!"))

            return self.render_json_response({
                'images': ','.join([str(x.pk) for x in self.get_object().images.all()]),
            })
        else:
            return super(UserCollectionsAddRemoveImages, self).post(request, *args, **kwargs)


class UserCollectionsDelete(
        LoginRequiredMixin, EnsureCollectionOwnerMixin, RedirectToCollectionListMixin,
        UserCollectionsBase, DeleteView):
    pk_url_kwarg = 'collection_pk'
    context_object_name = 'collection'

    def get_context_data(self, **kwargs):
        context = super(UserCollectionsDelete, self).get_context_data(**kwargs)
        context['delete_form'] = context.get('form')
        return context

    def post(self, *args, **kwargs):
        messages.success(self.request, _("Collection deleted!"))
        return super(UserCollectionsDelete, self).post(*args, **kwargs)


class UserCollectionsDetail(UserCollectionsBase, DetailView):
    pk_url_kwarg = 'collection_pk'
    context_object_name = 'collection'

    def get_context_data(self, **kwargs):
        context = super(UserCollectionsDetail, self).get_context_data(**kwargs)
        context['image_list'] = self.object.images.all()
        context['alias'] = 'gallery'
        return context

    def get_template_names(self):
        if self.request.is_ajax():
            return 'inclusion_tags/image_list_entries.html'
        return 'user_collections_detail.html'
