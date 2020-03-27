from braces.views import JSONResponseMixin, LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import UpdateView

from astrobin.models import Image
from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.mixins import RestrictToGroupMembersMixin, RestrictToNonAutosubmissionGroupsMixin


class GroupAddRemoveImages(
    JSONResponseMixin, LoginRequiredMixin, RestrictToGroupMembersMixin,
    RestrictToNonAutosubmissionGroupsMixin, UpdateView):
    model = Group
    fields = ('images',)
    template_name = 'astrobin_apps_groups/group_add_remove_images.html'

    def get_context_data(self, **kwargs):
        context = super(GroupAddRemoveImages, self).get_context_data(**kwargs)
        group = self.get_object()
        context['images'] = Image.objects.filter(user=self.request.user)
        context['images_pk_in_group'] = [x.pk for x in group.images.filter(user=self.request.user)]
        return context

    def get_success_url(self):
        return reverse('group_detail', kwargs={'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            group.images.remove(*Image.objects_including_wip.filter(user=request.user))
            images = Image.objects.filter(pk__in=request.POST.getlist('images[]'))
            if images:
                if images[0].user == request.user:
                    group.images.add(*images)
                    messages.success(request, _("Group updated with your selection of images."))
                else:
                    messages.error(request, _("You cannot add images that are not yours!"))
                    return super(GroupAddRemoveImages, self).post(request, *args, **kwargs)

                return self.render_json_response({
                    'images': ','.join([str(x.pk) for x in group.images.filter(user=request.user)]),
                })
        return super(GroupAddRemoveImages, self).post(request, *args, **kwargs)
