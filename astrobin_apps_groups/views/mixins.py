from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import View

from astrobin_apps_groups.models import Group
from astrobin_apps_groups.utils import has_access_to_premium_group_features
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free


class RestrictToGroupMembersMixin(View):
    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk = kwargs['pk'])
        if request.user not in group.members.all():
            return HttpResponseForbidden()
        return super(RestrictToGroupMembersMixin, self).dispatch(request, *args, **kwargs)


class RestrictToNonAutosubmissionGroupsMixin(View):
    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk = kwargs['pk'])
        if group.autosubmission:
            return HttpResponseForbidden()
        return super(RestrictToNonAutosubmissionGroupsMixin, self).dispatch(request, *args, **kwargs)


class RestrictToModeratedGroupsMixin(View):
    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk = kwargs['pk'])
        if not group.moderated:
            return HttpResponseForbidden()
        return super(RestrictToModeratedGroupsMixin, self).dispatch(request, *args, **kwargs)


class RestrictToGroupModeratorsMixin(View):
    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk = kwargs['pk'])
        if request.user not in group.moderators.all():
            return HttpResponseForbidden()
        return super(RestrictToGroupModeratorsMixin, self).dispatch(request, *args, **kwargs)


class RestrictToPremiumMembersMixin(View):
    def dispatch(self, request, *args, **kwargs):
        if not has_access_to_premium_group_features(request.user):
            return HttpResponseForbidden()
        return super(RestrictToPremiumMembersMixin, self).dispatch(request, *args, **kwargs)


class RedirectToGroupDetailMixin(View):
    def get_success_url(self):
        try:
            group = getattr(self, 'object')
        except AttributeError:
            group = self.get_object()
        return reverse('group_detail', kwargs = {'pk': group.pk})


class RestrictPrivateGroupToMembersMixin(View):
    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk = kwargs['pk'])
        if not (group.public or request.user == group.owner or request.user in group.members.all() or request.user in group.invited_users.all()):
            return HttpResponseForbidden()
        return super(RestrictPrivateGroupToMembersMixin, self).dispatch(request, *args, **kwargs)


class RestrictToGroupOwnerMixin(View):
    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk = kwargs['pk'])
        if request.user != group.owner:
            return HttpResponseForbidden()
        return super(RestrictToGroupOwnerMixin, self).dispatch(request, *args, **kwargs)
