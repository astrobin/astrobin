import simplejson
from braces.views import JSONResponseMixin
from braces.views import LoginRequiredMixin
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse_lazy
from django.db import IntegrityError
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic.base import View
from toggleproperties.models import ToggleProperty

from astrobin.forms import CollectionAddRemoveImagesForm
from astrobin.forms import CollectionCreateForm
from astrobin.forms import CollectionUpdateForm
from astrobin.forms import CollectionQuickEditKeyValueTagsForm
from astrobin.forms.utils import parseKeyValueTags
from astrobin.models import Collection
from astrobin.models import Image
from astrobin.models import UserProfile
from astrobin_apps_images.models import KeyValueTag


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
        try:
            user = UserProfile.objects.get(user__username=self.kwargs['username']).user
        except UserProfile.DoesNotExist:
            raise Http404

        image_ct = ContentType.objects.get_for_model(Image)

        context['requested_user'] = user
        context['public_images_no'] = Image.objects.filter(user = user).count()
        context['wip_images_no'] = Image.wip.filter(user = user).count()
        context['bookmarks_no'] = ToggleProperty.objects.toggleproperties_for_user("bookmark", user) \
            .filter(content_type = image_ct).count()
        context['likes_no'] = ToggleProperty.objects.toggleproperties_for_user("like", user) \
            .filter(content_type = image_ct).count()

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
        return context

    def get_template_names(self):
        if self.request.is_ajax():
            return 'inclusion_tags/image_list_entries.html'
        return 'user_collections_detail.html'
