from datetime import datetime
from typing import List
from urllib.parse import urlparse

import simplejson
from annoying.functions import get_object_or_None
from braces.views import JSONResponseMixin, LoginRequiredMixin
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Q, QuerySet
from django.forms.utils import ErrorList
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
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
from astrobin_apps_images.services import CollectionService
from astrobin_apps_users.services import UserService
from common.services import AppRedirectionService


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
        context['deleted_images_no'] = numbers['deleted_images_no']

        try:
            qs = UserService(user).get_public_images()
            context['mobile_header_background'] = \
                UserService(user).sort_gallery_by(qs, 'uploaded', None)[0] \
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

    def dispatch(self, request, *args, **kwargs):
        username: str = self.kwargs['username']
        profile = get_object_or_404(UserProfile, user__username=username)

        if profile.suspended:
            return render(request, 'user/suspended_account.html')

        if AppRedirectionService.should_redirect_to_new_gallery_experience(request):
            if profile.display_collections_on_public_gallery:
                fragment = 'gallery'
            else:
                fragment = 'collections'
            return redirect(AppRedirectionService.redirect(f'/u/{username}#{fragment}'))

        return super(UserCollectionsList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(parent__isnull=True)

    def get_context_data(self, **kwargs):
        context = super(UserCollectionsList, self).get_context_data(**kwargs)
        context['view'] = self.request.GET.get('view')
        return context


class UserCollectionsBaseEdit(LoginRequiredMixin, UserCollectionsBase, View):
    def form_valid(self, form):
        collection = form.save(commit=False)
        collection.user = self.request.user

        # Detect cycles
        x = collection.parent
        while x:
            if x == collection:
                form._errors["parent"] = ErrorList([_("Setting this collection as a parent would create a cycle")])
                return self.form_invalid(form)
            x = x.parent

        # Check if the cover has changed
        if 'cover' in form.cleaned_data and form.initial.get('cover') != form.cleaned_data['cover']:
            collection.cover = form.cleaned_data['cover']
            collection.update_cover(save=False)

        try:
            return super(UserCollectionsBaseEdit, self).form_valid(form)
        except IntegrityError:
            form._errors["name"] = ErrorList([_("You already have a collection with that name")])
            return self.form_invalid(form)


class UserCollectionsCreate(UserCollectionsBaseEdit, RedirectToCollectionListMixin, CreateView):
    form_class = CollectionCreateForm
    template_name = 'user_collections_create.html'

    def _get_referrer_collection_id(self):
        referrer = self.request.META.get('HTTP_REFERER')

        if referrer:
            path = urlparse(referrer).path
            path_parts = [part for part in path.split('/') if part]
            collection_id = path_parts[-1] if path_parts[-1].isdigit() else None
            return collection_id

        return None

    def get_form_kwargs(self):
        kwargs = super(UserCollectionsCreate, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})

        referrer_collection_id = self._get_referrer_collection_id()
        if referrer_collection_id:
            kwargs.update({'initial': {'parent': referrer_collection_id}})

        return kwargs

    def get_success_url(self) -> str:
        collection = self.object
        if collection.parent:
            return reverse_lazy(
                'user_collections_detail',
                args=(collection.parent.user.username, collection.parent.pk,)
            )

        return super().get_success_url()


class UserCollectionsUpdate(
    RedirectToCollectionListMixin, EnsureCollectionOwnerMixin,
    UserCollectionsBaseEdit, UpdateView):
    form_class = CollectionUpdateForm
    template_name = 'user_collections_update.html'
    pk_url_kwarg = 'collection_pk'
    context_object_name = 'collection'

    def get_form(self, form_class=None):
        form = super(UserCollectionsUpdate, self).get_form(form_class)
        descendants = CollectionService(self.object).get_descendant_collections()

        image_queryset = Image.objects.none()
        for collection in descendants:
            image_queryset = image_queryset | collection.images.all()

        form.fields['cover'].queryset = image_queryset.distinct()

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
        context['images'] = UserService(user).get_all_images()
        context['images_pk_in_collection'] = [
            x.pk for x in Image.objects_including_wip.filter(collections=self.get_object())
        ]
        return context

    def get_success_url(self):
        return reverse_lazy('user_collections_detail', args=(self.kwargs['username'], self.kwargs['collection_pk'],))

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            collection: Collection = self.get_object()
            image_pks: List[int] = request.POST.getlist('images[]')
            images: QuerySet = Image.objects_including_wip.filter(
                Q(Q(user=request.user) | Q(collaborators=request.user)) &
                Q(pk__in=image_pks)
            )

            CollectionService(collection).add_remove_images(images)
            images.update(updated=datetime.now())

            messages.success(request, _("Collection updated!"))

            if images.filter(is_wip=True).exists():
                messages.warning(
                    request,
                    _("Please note: some of the images you added are in your staging area and won't be visible to "
                      "visitors of this collection.")
                )

            return self.render_json_response({
                'images': ','.join(
                    [str(x.pk) for x in Image.objects_including_wip.filter(collections=self.get_object())]
                ),
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
        context['images'] = Image.objects_including_wip.filter(collections=self.get_object())
        return context

    def get_success_url(self):
        return reverse_lazy('user_collections_detail', args=(self.kwargs['username'], self.kwargs['collection_pk'],))

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            for data in simplejson.loads(request.POST.get('imageData')):
                image = Image.objects_including_wip.get(pk=data['image_pk'])
                try:
                    parsed = parseKeyValueTags(data['value'])
                    image.keyvaluetags.all().delete()
                    for tag in parsed:
                        KeyValueTag.objects.get_or_create(
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
                'images': ','.join(
                    [str(x.pk) for x in Image.objects_including_wip.filter(collections=self.get_object())]
                ),
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

    def dispatch(self, request, *args, **kwargs):
        response = super(UserCollectionsDetail, self).dispatch(request, *args, **kwargs)
        request.collection = self.object
        profile = self.object.user.userprofile

        if profile.suspended:
            return render(request, 'user/suspended_account.html')

        if AppRedirectionService.should_redirect_to_new_gallery_experience(request):
            if profile.display_collections_on_public_gallery:
                fragment = 'gallery'
            else:
                fragment = 'collections'
            return redirect(
                AppRedirectionService.redirect(f'/u/{self.object.user.username}?collection={self.object.id}#{fragment}')
            )

        return response

    def get_context_data(self, **kwargs):
        context = super(UserCollectionsDetail, self).get_context_data(**kwargs)

        image_list = Image.objects_including_wip.filter(
            collections=self.object
        )
        not_matching_tag = None

        if self.object.order_by_tag:
            image_list = image_list \
                .filter(keyvaluetags__key=self.object.order_by_tag) \
                .order_by("keyvaluetags__value")
            not_matching_tag = Image.objects_including_wip.filter(collections=self.object) \
                .exclude(keyvaluetags__key=self.object.order_by_tag)

        if self.request.user != self.object.user:
            image_list = image_list.filter(is_wip=False)
            if not_matching_tag:
                not_matching_tag = not_matching_tag.filter(is_wip=False)

        context['image_list'] = image_list
        context['not_matching_tag'] = not_matching_tag
        context['image_list_count'] = image_list.count()
        context['not_matching_tag_count'] = not_matching_tag.count() if not_matching_tag else 0
        context['alias'] = 'gallery'
        context['paginate_by'] = settings.PAGINATE_USER_PAGE_BY
        return context

    def get_template_names(self):
        if self.request.is_ajax():
            return 'inclusion_tags/image_list_entries.html'
        return 'user_collections_detail.html'


class UserCollectionsNoCollection(View):
    model = Image

    def get(self, request, *args, **kwargs):
        username = self.kwargs['username']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise Http404

        if request.user != user:
            return HttpResponseForbidden()

        image_list = Image.objects_including_wip.filter(user__username=username, collections__isnull=True)
        context = {
            'requested_user': user,
            'username': user.userprofile.get_display_name(),
            'image_list': image_list,
            'image_list_count': image_list.count(), 'alias': 'gallery',
            'paginate_by': settings.PAGINATE_USER_PAGE_BY,
        }

        if self.request.is_ajax():
            return render(self.request, 'inclusion_tags/image_list_entries.html', context)

        return render(self.request, 'user_collections_detail.html', context)
