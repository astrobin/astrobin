from braces.views import JSONResponseMixin, LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.views.generic import UpdateView

from astrobin.models import UserProfile
from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.mixins import RestrictToGroupOwnerMixin, RestrictToModeratedGroupsMixin


class GroupRemoveModerator(
    JSONResponseMixin, LoginRequiredMixin, RestrictToGroupOwnerMixin,
    RestrictToModeratedGroupsMixin, UpdateView):
    model = Group

    def get_success_url(self):
        return reverse('group_detail', kwargs={'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            user = UserProfile.objects.get(user__pk=self.request.POST.get('user')).user
            if user not in group.moderators.all():
                return HttpResponseForbidden()
            group.moderators.remove(user)
            group.forum.moderators.remove(user)
            return self.render_json_response({
                'moderator': {
                    'pk': user.pk,
                    'add_url': reverse('group_add_moderator', args=(group.pk,)),
                },
            })

        # Only AJAX allowed
        return HttpResponseForbidden()
