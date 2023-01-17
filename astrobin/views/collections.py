import simplejson
from annoying.functions import get_object_or_None
from braces.views import JSONResponseMixin, LoginRequiredMixin
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.forms.utils import ErrorList
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.base import View

from astrobin.forms import (
    CollectionAddRemoveImagesForm, CollectionCreateForm, CollectionQuickEditKeyValueTagsForm,
    CollectionUpdateForm,
)
from astrobin.forms.utils import parseKeyValueTags
from astrobin.models import Collection, Image, UserProfile
from astrobin_apps_images.models import KeyValueTag
from astrobin_apps_users.services import UserService


class EnsureCollectionOwnerMixin(View):
    def dispatch(self, request, *args, **kwargs):
        collection = get_object_or_404(Collection, pk=kwargs[self.pk_url_kwarg])
        if request.user != collection.user:
            return HttpResponseForbidden

        return super(EnsureCollectionOwnerMixin, self).dispatch(request, *args, **kwargs)


class RedirectToCollectionListMixin():
    def get_success_url(self):
        return reverse_lazy('user_collections_list', args=(self.kwargs['username'],))


class UserCollectionsBase(View):
    model = Collection

    def get_queryset(self):
        qs = super(UserCollectionsBase, self).get_queryset()
        return qs.filter(user__username=self.kwargs['username'])

    def get_context_data(self, **kwargs):
        context = super(UserCollectionsBase, self).get_context_data(**kwargs)
        try:
            user = UserProfile.objects.get(user__username=self.kwargs['username']).user
        except UserProfile.DoesNotExist:
            raise Http404

        context['requested_user'] = user

        numbers = UserService(user).get_image_numbers()
        context['public_images_no'] = numbers['public_images_no']
        context['wip_images_no'] = numbers['wip_images_no']

        try:
            qs = UserService(user).get_public_images()
            context['mobile_header_background'] = \
                UserService(user).sort_gallery_by(qs, 'uploaded', None, None)[0] \
                    .first() \
                    .thumbnail('regular', None, sync=True) \
                    if UserService(user).get_public_images().exists() \
                    else None
        except IOError:
            context['mobile_header_background'] = None

        stats_data = UserService(user).get_profile_stats(getattr(self.request, 'LANGUAGE_CODE', 'en'))
        context['stats'] = stats_data['stats'] if 'stats' in stats_data else None

        return context


class UserCollectionsList(UserCollectionsBase, ListView):
    template_name = 'user_collections_list.html'
    context_object_name = 'collections_list'

    def get_context_data(self, **kwargs):
        context = super(UserCollectionsList, self).get_context_data(**kwargs)

        context['non_empty_collections_count'] = self.get_queryset().exclude(images=None).count()
        context['view'] = self.request.GET.get('view')
        return context


class UserCollectionsBaseEdit(LoginRequiredMixin, UserCollectionsBase, View):
    def form_valid(self, form):
        collection = form.save(commit=False)
        collection.user = self.request.user
        try:
            return super(UserCollectionsBaseEdit, self).form_valid(form)
        except IntegrityError:
            form._errors["name"] = ErrorList([_("You already have a collection with that name")])
            return self.form_invalid(form)


class UserCollectionsCreate(
    UserCollectionsBaseEdit, RedirectToCollectionListMixin, CreateView):
    form_class = CollectionCreateForm
    template_name = 'user_collections_create.html'

    def get_form_kwargs(self):
        kwargs = super(UserCollectionsCreate, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs


class UserCollectionsUpdate(
    RedirectToCollectionListMixin, EnsureCollectionOwnerMixin,
    UserCollectionsBaseEdit, UpdateView):
    form_class = CollectionUpdateForm
    template_name = 'user_collections_update.html'
    pk_url_kwarg = 'collection_pk'
    context_object_name = 'collection'

    def get_form(self, form_class=None):
        form = super(UserCollectionsUpdate, self).get_form(form_class)
        form.fields['cover'].queryset = Collection.objects.get(pk=self.kwargs['collection_pk']).images.all()
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
        user = get_object_or_None(User, username=self.kwargs.get('username'))
        context['images'] = UserService(user).get_public_images()
        context['images_pk_in_collection'] = [x.pk for x in self.get_object().images.all()]
        return context

    def get_success_url(self):
        return reverse_lazy('user_collections_detail', args=(self.kwargs['username'], self.kwargs['collection_pk'],))

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            self.get_object().images.clear()
            for pk in request.POST.getlist('images[]'):
                image = Image.objects.get(pk=pk)
                self.get_object().images.add(image)

            messages.success(request, _("Collection updated!"))

            return self.render_json_response({
                'images': ','.join([str(x.pk) for x in self.get_object().images.all()]),
            })
        else:
            return super(UserCollectionsAddRemoveImages, self).post(request, *args, **kwargs)


class UserCollectionsQuickEditKeyValueTags(
    JSONResponseMixin, EnsureCollectionOwnerMixin, UserCollectionsBaseEdit, UpdateView):
    form_class = CollectionQuickEditKeyValueTagsForm
    template_name = 'user_collections_quick_edit_key_value_tags.html'
    pk_url_kwarg = 'collection_pk'
    context_object_name = 'collection'
    content_type = None

    def get_context_data(self, **kwargs):
        context = super(UserCollectionsQuickEditKeyValueTags, self).get_context_data(**kwargs)
        context['images'] = self.get_object().images.all()
        return context

    def get_success_url(self):
        return reverse_lazy('user_collections_detail', args=(self.kwargs['username'], self.kwargs['collection_pk'],))

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            for data in simplejson.loads(request.POST.get('imageData')):
                image = Image.objects.get(pk=data['image_pk'])
                try:
                    parsed = parseKeyValueTags(data['value'])
                    image.keyvaluetags.all().delete()
                    for tag in parsed:
                        KeyValueTag.objects.create(
                            image=image,
                            key=tag["key"],
                            value=tag["value"]
                        )

                except ValueError:
                    return self.render_json_response({
                        'error': _(
                            "Provide a list of unique key/value pairs to tag this image with. Use the '=' symbol "
                            "between key and value, and provide one pair per line. These tags can be used to sort "
                            "images by arbitrary properties."),
                        'image_pk': data['image_pk']
                    })

            messages.success(request, _("Images updated!"))

            return self.render_json_response({
                'images': ','.join([str(x.pk) for x in self.get_object().images.all()]),
            })
        else:
            return super(UserCollectionsQuickEditKeyValueTags, self).post(request, *args, **kwargs)


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

        image_list = self.object.images
        not_matching_tag = None

        if self.object.order_by_tag:
            image_list = image_list \
                .filter(keyvaluetags__key=self.object.order_by_tag) \
                .order_by("keyvaluetags__value")
            not_matching_tag = self.object.images \
                .exclude(keyvaluetags__key=self.object.order_by_tag)

        context['image_list'] = image_list.all() if image_list else None
        context['not_matching_tag'] = not_matching_tag.all() if not_matching_tag else None
        context['alias'] = 'gallery'
        context['paginate_by'] = settings.PAGINATE_USER_PAGE_BY
        return context

    def get_template_names(self):
        if self.request.is_ajax():
            return 'inclusion_tags/image_list_entries.html'
        return 'user_collections_detail.html'
