# Django
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.views.generic import CreateView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import UpdateView
from django.views.generic.base import View
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

# Third party
from braces.views import JSONResponseMixin
from braces.views import LoginRequiredMixin

# This app
from astrobin_apps_groups.forms import *
from astrobin_apps_groups.models import *


# Mixins

class RestrictPrivateGroupToMembersMixin(View):
    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk = kwargs['pk'])
        if not (group.public or request.user == group.owner or request.user in group.members.all()):
            return HttpResponseForbidden()
        return super(RestrictPrivateGroupToMembersMixin, self).dispatch(request, *args, **kwargs)


class RestrictToGroupOwnerMixin(View):
    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk = kwargs['pk'])
        if request.user != group.owner:
            return HttpResponseForbidden()
        return super(RestrictToGroupOwnerMixin, self).dispatch(request, *args, **kwargs)


class RedirectToGroupDetailMixin(View):
    def get_success_url(self):
        try:
            group = getattr(self, 'object')
        except AttributeError:
            group = self.get_object()
        return reverse('group_detail', kwargs = {'pk': group.pk})


# Views

class PublicGroupListView(ListView):
    queryset = Group.objects.filter(public = True)
    template_name = 'astrobin_apps_groups/public_group_list.html'


class GroupDetailView(RestrictPrivateGroupToMembersMixin, DetailView):
    model = Group
    template_name = 'astrobin_apps_groups/group_detail.html'


class GroupCreateView(LoginRequiredMixin, RedirectToGroupDetailMixin, CreateView):
    form_class = GroupCreateForm
    template_name = 'astrobin_apps_groups/group_create.html'

    def form_valid(self, form):
        group = form.save(commit = False)
        group.creator = self.request.user
        group.owner = self.request.user
        messages.success(self.request, _("Your new group was created successfully"))
        return super(GroupCreateView, self).form_valid(form)


class GroupUpdateView(LoginRequiredMixin, RestrictToGroupOwnerMixin, RedirectToGroupDetailMixin, UpdateView):
    form_class = GroupUpdateForm
    model = Group
    template_name = 'astrobin_apps_groups/group_update.html'

    def form_valid(self, form):
        messages.success(self.request, _("Form saved"))
        return super(GroupUpdateView, self).form_valid(form)


class GroupJoinView(LoginRequiredMixin, RedirectToGroupDetailMixin, UpdateView):
    http_method_names = ['post',]
    model = Group

    def post(self, request, *args, **kwargs):
        group = self.get_object()

        if request.user in group.members.all():
            messages.error(request, _("You already were a member of this group"))
            return redirect(self.get_success_url())

        if group.public or request.user in group.invited_users.all():
            group.members.add(request.user)
            messages.success(request, _("You have joined the group"))
            return redirect(self.get_success_url())

        return HttpResponseForbidden()


class GroupManageMembersView(LoginRequiredMixin, RestrictToGroupOwnerMixin, RedirectToGroupDetailMixin, UpdateView):
    form_class = GroupInviteForm
    model = Group
    template_name = 'astrobin_apps_groups/group_manage_members.html'


class GroupInviteView(
        JSONResponseMixin, LoginRequiredMixin, RestrictToGroupOwnerMixin,
        RedirectToGroupDetailMixin, UpdateView):
    form_class = GroupInviteForm
    model = Group
    template_name = 'astrobin_apps_groups/group_invite.html'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        group = self.get_object()
        for pk in request.POST.getlist('users[]'):
            try:
                user = User.objects.get(pk = pk)
            except User.DoesNotExist:
                continue

            group.invited_users.add(user)

        if request.is_ajax():
            return self.render_json_response({
                'invited_users': [{
                    'id': x.id,
                    'username': x.username,
                    'display_name': x.userprofile.get_display_name(),
                    'url': reverse('user_page', args = (x.username,)),
                    'revoke_url': reverse('group_revoke_invitation', args = (group.pk,)),
                } for x in group.invited_users.all()]
            })

        return redirect(self.get_success_url())


class GroupRevokeInvitationView(
        JSONResponseMixin, LoginRequiredMixin, RestrictToGroupOwnerMixin,
        RedirectToGroupDetailMixin, UpdateView):
    model = Group
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        group = self.get_object()
        user = get_object_or_404(User, username = request.POST.get('user'))
        group.invited_users.remove(user)

        if request.is_ajax():
            return self.render_json_response({
                'invited_users': [{
                    'id': x.id,
                    'username': x.username,
                    'display_name': x.userprofile.get_display_name(),
                    'url': reverse('user_page', args = (x.username,)),
                    'revoke_url': reverse('group_revoke_invitation', args = (group.pk,)),
                } for x in group.invited_users.all()]
            })

        return redirect(self.get_success_url())
