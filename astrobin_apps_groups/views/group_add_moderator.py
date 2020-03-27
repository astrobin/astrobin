from braces.views import JSONResponseMixin, LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.views.generic import UpdateView

from astrobin.models import UserProfile
from astrobin_apps_groups.models import Group
from astrobin_apps_groups.views.mixins import RestrictToGroupOwnerMixin, RestrictToModeratedGroupsMixin


class GroupAddModerator(
    JSONResponseMixin, LoginRequiredMixin, RestrictToGroupOwnerMixin,
    RestrictToModeratedGroupsMixin, UpdateView):
    model = Group

    def get_success_url(self):
        return reverse('group_detail', kwargs={'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            user = UserProfile.objects.get(user__pk=self.request.POST.get('user')).user
            if user not in group.members.all():
                return HttpResponseForbidden()
            group.moderators.add(user)
            group.forum.moderators.add(user)
            return self.render_json_response({
                'moderators': [{
                    'pk': x.pk,
                    'url': reverse('user_page', args=(x.username,)),
                    'display_name': x.userprofile.get_display_name(),
                    'remove_url': reverse('group_remove_moderator', args=(group.pk,)),
                } for x in group.moderators.all()]
            })

        # Only AJAX allowed
        return HttpResponseForbidden()
