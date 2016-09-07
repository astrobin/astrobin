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

# AstroBin
from astrobin_apps_notifications.utils import push_notification

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

    def get_template_names(self):
        if self.request.is_ajax():
            return 'inclusion_tags/image_list_entries.html'
        return 'astrobin_apps_groups/group_detail.html'

    def get_context_data(self, **kwargs):
        context = super(GroupDetailView, self).get_context_data(**kwargs)
        group = self.get_object()

        # Images
        context['image_list'] = group.images.all()
        context['alias'] = 'gallery'

        # Misc
        context['user_is_member'] = self.request.user in group.members.all()
        context['user_is_invited'] = self.request.user in group.invited_users.all()

        return context


class GroupCreateView(LoginRequiredMixin, RedirectToGroupDetailMixin, CreateView):
    form_class = GroupCreateForm
    template_name = 'astrobin_apps_groups/group_create.html'

    def form_valid(self, form):
        group = form.save(commit = False)
        group.creator = self.request.user
        group.owner = self.request.user
        if group.moderated:
            group.save() # Need to save before I can have a m2m
            group.moderators.add(group.owner)
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
            if group.moderated:
                group.join_requests.add(request.user)
                messages.warning(request, _("This is a moderated group, and your join request will be reviewed by a moderator"))
                push_notification(group.moderators.all(), 'new_group_join_request',
                    {
                        'requester': request.user.userprofile.get_display_name(),
                        'group_name': group.name,
                        'url': reverse('group_manage_members', args = (group.pk,)),
                    })
            else:
                group.members.add(request.user)
                group.invited_users.remove(request.user)
                messages.success(request, _("You have joined the group"))
            return redirect(self.get_success_url())

        return HttpResponseForbidden()


class GroupLeaveView(
        LoginRequiredMixin, RedirectToGroupDetailMixin,
        RestrictToGroupMembersMixin, UpdateView):
    http_method_names = ['post',]
    model = Group

    def post(self, request, *args, **kwargs):
        group = self.get_object()

        if request.user not in group.members.all():
            return HttpResponseForbidden()

        group.members.remove(request.user)
        if not group.autosubmission:
            group.images.remove(*Image.objects.filter(user = request.user))
        messages.success(request, _("You have left the group"))

        if group.public:
            return redirect(self.get_success_url())
        return redirect(reverse('public_group_list'))


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
            push_notification([user], 'new_group_invitation',
                {
                    'inviter': request.user.userprofile.get_display_name(),
                    'inviter_page': reverse('user_page', args = (request.user.username,)),
                    'group_name': group.name,
                    'group_page': reverse('group_detail', args = (group.pk,)),
                })

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


class GroupAddRemoveImages(
        JSONResponseMixin, LoginRequiredMixin, RestrictToGroupMembersMixin,
        RestrictToNonAutosubmissionGroupsMixin, UpdateView):
    model = Group
    template_name = 'astrobin_apps_groups/group_add_remove_images.html'

    def get_context_data(self, **kwargs):
        context = super(GroupAddRemoveImages, self).get_context_data(**kwargs)
        group = self.get_object()
        context['images'] = Image.objects.filter(user = self.request.user)
        context['images_pk_in_group'] = [x.pk for x in group.images.filter(user = self.request.user)]
        return context

    def get_success_url(self):
        return reverse('group_detail', kwargs = {'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            group.images.remove(*Image.all_objects.filter(user = request.user))
            for pk in request.POST.getlist('images[]'):
                image = Image.objects.get(pk = pk)
                if (image.user == request.user):
                    group.images.add(image)
                else:
                    message.error(request, _("You cannot add images that are not yours!"))
                    return super(GroupAddRemoveImages, self).post(request, *args, **kwargs)

            messages.success(request, _("Group updated with your selection of images."))

            return self.render_json_response({
                'images': ','.join([str(x.pk) for x in group.images.filter(user = request.user)]),
            })
        return super(GroupAddRemoveImages, self).post(request, *args, **kwargs)


class GroupAddImage(
        JSONResponseMixin, LoginRequiredMixin, RestrictToGroupMembersMixin,
        RestrictToNonAutosubmissionGroupsMixin, UpdateView):
    model = Group

    def get_success_url(self):
        return reverse('group_detail', kwargs = {'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            image = Image.objects.get(pk = self.request.POST.get('image'))
            if (image.user == request.user):
                group.images.add(image)
            else:
                message.error(request, _("You cannot add images that are not yours!"))
                return super(GroupAddImages, self).post(request, *args, **kwargs)

            messages.success(request, _("Your image was added to the group."))

            return self.render_json_response({
                'image': image.pk,
            })

        # Only AJAX allowed
        return HttpResponseForbidden()
