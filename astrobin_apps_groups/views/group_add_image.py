from braces.views import JSONResponseMixin, LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import UpdateView

from astrobin.models import Image
from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.mixins import RestrictToGroupMembersMixin, RestrictToNonAutosubmissionGroupsMixin


class GroupAddImage(
    JSONResponseMixin, LoginRequiredMixin, RestrictToGroupMembersMixin,
    RestrictToNonAutosubmissionGroupsMixin, UpdateView):
    model = Group

    def get_success_url(self):
        return reverse('group_detail', kwargs={'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            image = Image.objects.get(pk=self.request.POST.get('image'))
            if (image.user == request.user):
                group.images.add(image)
            else:
                message.error(request, _("You cannot add images that are not yours!"))
                return super(GroupAddImage, self).post(request, *args, **kwargs)

            messages.success(request, _("Your image was added to the group."))

            return self.render_json_response({
                'image': image.pk,
            })

        # Only AJAX allowed
        return HttpResponseForbidden()
