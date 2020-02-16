from braces.views import LoginRequiredMixin, JSONResponseMixin
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from pybb.permissions import perms

from astrobin_apps_groups.forms import GroupCreateForm, GroupInviteForm, GroupUpdateForm
from astrobin_apps_groups.models import Group
from astrobin_apps_notifications.utils import push_notification


class RestrictPrivateGroupToMembersMixin(View):
    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk=kwargs['pk'])
        if not (
                group.public or request.user == group.owner or request.user in group.members.all() or request.user in group.invited_users.all()):
            return HttpResponseForbidden()
        return super(RestrictPrivateGroupToMembersMixin, self).dispatch(request, *args, **kwargs)


class RestrictToGroupOwnerMixin(View):
    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk=kwargs['pk'])
        if request.user != group.owner:
            return HttpResponseForbidden()
        return super(RestrictToGroupOwnerMixin, self).dispatch(request, *args, **kwargs)


class RestrictToGroupMembersMixin(View):
    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk=kwargs['pk'])
        if request.user not in group.members.all():
            return HttpResponseForbidden()
        return super(RestrictToGroupMembersMixin, self).dispatch(request, *args, **kwargs)


class RestrictToNonAutosubmissionGroupsMixin(View):
    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk=kwargs['pk'])
        if group.autosubmission:
            return HttpResponseForbidden()
        return super(RestrictToNonAutosubmissionGroupsMixin, self).dispatch(request, *args, **kwargs)


class RestrictToModeratedGroupsMixin(View):
    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk=kwargs['pk'])
        if not group.moderated:
            return HttpResponseForbidden()
        return super(RestrictToModeratedGroupsMixin, self).dispatch(request, *args, **kwargs)


class RestrictToGroupModeratorsMixin(View):
    def dispatch(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk=kwargs['pk'])
        if request.user not in group.moderators.all():
            return HttpResponseForbidden()
        return super(RestrictToGroupModeratorsMixin, self).dispatch(request, *args, **kwargs)


class RedirectToGroupDetailMixin(View):
    def get_success_url(self):
        try:
            group = getattr(self, 'object')
        except AttributeError:
            group = self.get_object()
        return reverse('group_detail', kwargs={'pk': group.pk})

    # Views


class GroupListView(ListView):
    model = Group
    template_name = 'astrobin_apps_groups/group_list.html'

    def get_context_data(self, **kwargs):
        context = super(GroupListView, self).get_context_data(**kwargs)

        sort = self.request.GET.get('sort', 'activity')
        try:
            sort = {
                'name': 'name',
                'category': 'category',
                'created': '-date_created',
                'activity': '-date_updated',
                'posts': '-forum__post_count',
            }[sort]
        except KeyError:
            pass

        if self.request.user.is_authenticated():
            context['private_groups'] = \
                self.get_queryset() \
                    .filter(public=False) \
                    .filter(
                    Q(owner=self.request.user) |
                    Q(members=self.request.user) |
                    Q(invited_users=self.request.user)) \
                    .distinct() \
                    .order_by(sort)

        context['public_groups'] = \
            self.get_queryset().filter(public=True).order_by(sort)

        return context


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
        context['image_list'] = group.images \
            .exclude(Q(is_wip=True) | Q(corrupted=True)) \
            .filter(deleted=None)
        context['alias'] = 'gallery'

        # Misc
        context['user_is_member'] = self.request.user in group.members.all()
        context['user_is_invited'] = self.request.user in group.invited_users.all()
        context['user_is_moderator'] = self.request.user in group.moderators.all()

        # Forum
        topics = group.forum.topics.order_by('-sticky', '-updated', '-id').select_related()
        topics = perms.filter_topics(self.request.user, topics)
        context['topics'] = topics[:5]

        return context


class GroupCreateView(LoginRequiredMixin, RedirectToGroupDetailMixin, CreateView):
    form_class = GroupCreateForm
    template_name = 'astrobin_apps_groups/group_create.html'

    def get_initial(self):
        if 'public' in self.request.GET:
            return {
                'public': self.request.GET.get('public')
            };

        return super(GroupCreateView, self).get_initial()

    def form_valid(self, form):
        group = form.save(commit=False)
        group.creator = self.request.user
        group.owner = self.request.user

        messages.success(self.request, _("Your new group was created successfully"))
        return super(GroupCreateView, self).form_valid(form)


class GroupUpdateView(LoginRequiredMixin, RestrictToGroupOwnerMixin, RedirectToGroupDetailMixin, UpdateView):
    form_class = GroupUpdateForm
    model = Group
    template_name = 'astrobin_apps_groups/group_update.html'

    def form_valid(self, form):
        group = self.get_object()
        if (group.images.count() > 0 and
                group.autosubmission and
                not form.cleaned_data['autosubmission'] and
                form.cleaned_data['autosubmission_deactivation_strategy'] == 'delete'):
            group.images.clear()
        messages.success(self.request, _("Form saved"))
        return super(GroupUpdateView, self).form_valid(form)


class GroupDeleteView(LoginRequiredMixin, RestrictToGroupOwnerMixin, DeleteView):
    model = Group
    success_url = reverse_lazy('group_list')

    def form_valid(self, form):
        messages.success(self.request, _("Group deleted"))
        return super(GroupUpdateView, self).form_valid(form)


class GroupJoinView(LoginRequiredMixin, RedirectToGroupDetailMixin, UpdateView):
    http_method_names = ['post', ]
    model = Group

    def post(self, request, *args, **kwargs):
        group = self.get_object()

        def doAdd(user, group):
            group.members.add(user)
            group.invited_users.remove(user)
            group.join_requests.remove(user)
            messages.success(request, _("You have joined the group"))

        if request.user in group.members.all():
            messages.error(request, _("You already were a member of this group"))
            return redirect(self.get_success_url())

        if group.public:
            if group.moderated and request.user != group.owner:
                group.join_requests.add(request.user)
                messages.warning(request,
                                 _("This is a moderated group, and your join request will be reviewed by a moderator"))
                push_notification(group.moderators.all(), 'new_group_join_request',
                                  {
                                      'requester': request.user.userprofile.get_display_name(),
                                      'group_name': group.name,
                                      'url': settings.BASE_URL + reverse('group_moderate_join_requests',
                                                                         args=(group.pk,)),
                                  })
                return redirect(self.get_success_url())
            else:
                doAdd(request.user, group)
                return redirect(self.get_success_url())
        else:
            if request.user in group.invited_users.all() or request.user == group.owner:
                doAdd(request.user, group)
                return redirect(self.get_success_url())

        return HttpResponseForbidden()


class GroupLeaveView(
    LoginRequiredMixin, RedirectToGroupDetailMixin,
    RestrictToGroupMembersMixin, UpdateView):
    http_method_names = ['post', ]
    model = Group

    def post(self, request, *args, **kwargs):
        group = self.get_object()

        if request.user not in group.members.all():
            return HttpResponseForbidden()

        group.members.remove(request.user)
        messages.success(request, _("You have left the group"))

        if group.public:
            return redirect(self.get_success_url())
        return redirect(reverse('group_list'))


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
                from astrobin.models import UserProfile
                user = UserProfile.objects.get(user__pk=pk).user
            except UserProfile.DoesNotExist:
                continue

            group.invited_users.add(user)
            push_notification([user], 'new_group_invitation',
                              {
                                  'inviter': request.user.userprofile.get_display_name(),
                                  'inviter_page': reverse('user_page', args=(request.user.username,)),
                                  'group_name': group.name,
                                  'group_page': settings.BASE_URL + reverse('group_detail', args=(group.pk,)),
                              })

        if request.is_ajax():
            return self.render_json_response({
                'invited_users': [{
                    'id': x.id,
                    'username': x.username,
                    'display_name': x.userprofile.get_display_name(),
                    'url': reverse('user_page', args=(x.username,)),
                    'revoke_url': reverse('group_revoke_invitation', args=(group.pk,)),
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
        user = get_object_or_404(User, username=request.POST.get('user'))
        group.invited_users.remove(user)

        if request.is_ajax():
            return self.render_json_response({
                'invited_users': [{
                    'id': x.id,
                    'username': x.username,
                    'display_name': x.userprofile.get_display_name(),
                    'url': reverse('user_page', args=(x.username,)),
                    'revoke_url': reverse('group_revoke_invitation', args=(group.pk,)),
                } for x in group.invited_users.all()]
            })

        return redirect(self.get_success_url())


class GroupAddRemoveImages(
    JSONResponseMixin, LoginRequiredMixin, RestrictToGroupMembersMixin,
    RestrictToNonAutosubmissionGroupsMixin, UpdateView):
    model = Group
    fields = ('images',)
    template_name = 'astrobin_apps_groups/group_add_remove_images.html'

    def get_context_data(self, **kwargs):
        context = super(GroupAddRemoveImages, self).get_context_data(**kwargs)
        group = self.get_object()
        from astrobin.models import Image
        context['images'] = Image.objects.filter(user=self.request.user)
        context['images_pk_in_group'] = [x.pk for x in group.images.filter(user=self.request.user)]
        return context

    def get_success_url(self):
        return reverse('group_detail', kwargs={'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            from astrobin.models import Image
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


class GroupAddImage(
    JSONResponseMixin, LoginRequiredMixin, RestrictToGroupMembersMixin,
    RestrictToNonAutosubmissionGroupsMixin, UpdateView):
    model = Group

    def get_success_url(self):
        return reverse('group_detail', kwargs={'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            from astrobin.models import Image
            image = Image.objects.get(pk=self.request.POST.get('image'))
            if (image.user == request.user):
                group.images.add(image)
            else:
                messages.error(request, _("You cannot add images that are not yours!"))
                return super(GroupAddImage, self).post(request, *args, **kwargs)

            messages.success(request, _("Your image was added to the group."))

            return self.render_json_response({
                'image': image.pk,
            })

        # Only AJAX allowed
        return HttpResponseForbidden()


class GroupAddModerator(
    JSONResponseMixin, LoginRequiredMixin, RestrictToGroupOwnerMixin,
    RestrictToModeratedGroupsMixin, UpdateView):
    model = Group

    def get_success_url(self):
        return reverse('group_detail', kwargs={'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            from astrobin.models import UserProfile
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


class GroupRemoveModerator(
    JSONResponseMixin, LoginRequiredMixin, RestrictToGroupOwnerMixin,
    RestrictToModeratedGroupsMixin, UpdateView):
    model = Group

    def get_success_url(self):
        return reverse('group_detail', kwargs={'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            from astrobin.models import UserProfile
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


class GroupRemoveMember(
    JSONResponseMixin, LoginRequiredMixin, RestrictToGroupOwnerMixin,
    UpdateView):
    model = Group

    def get_success_url(self):
        return reverse('group_detail', kwargs={'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            from astrobin.models import UserProfile
            user = UserProfile.objects.get(user__pk=self.request.POST.get('user')).user
            if user not in group.members.all():
                return HttpResponseForbidden()
            group.members.remove(user)
            return self.render_json_response({
                'member': user.pk,
            })

        # Only AJAX allowed
        return HttpResponseForbidden()


class GroupMembersListView(LoginRequiredMixin, RestrictPrivateGroupToMembersMixin, DetailView):
    model = Group
    template_name = 'astrobin_apps_groups/group_members_list.html'


class GroupModerateJoinRequestsView(LoginRequiredMixin, RestrictToModeratedGroupsMixin,
                                    RestrictToGroupModeratorsMixin, DetailView):
    model = Group
    template_name = 'astrobin_apps_groups/group_moderate_join_requests.html'


class GroupApproveJoinRequestView(JSONResponseMixin, LoginRequiredMixin,
                                  RestrictToModeratedGroupsMixin, RestrictToGroupModeratorsMixin,
                                  UpdateView):
    model = Group

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            from astrobin.models import UserProfile
            user = UserProfile.objects.get(user__pk=self.request.POST.get('user')).user

            if user not in group.join_requests.all():
                return HttpResponseForbidden()

            group.join_requests.remove(user)
            group.members.add(user)
            push_notification([user], 'group_join_request_approved',
                              {
                                  'group_name': group.name,
                                  'url': settings.BASE_URL + reverse('group_detail', args=(group.pk,)),
                              })

            return self.render_json_response({
                'member': user.pk,
            })

        # Only AJAX allowed
        return HttpResponseForbidden()


class GroupRejectJoinRequestView(JSONResponseMixin, LoginRequiredMixin,
                                 # RestrictToModeratedGroupsMixin, RestrictToGroupModeratorsMixin,
                                 UpdateView):
    model = Group

    def post(self, request, *args, **kwargs):
        if request.is_ajax():
            group = self.get_object()
            from astrobin.models import UserProfile
            user = UserProfile.objects.get(user__pk=self.request.POST.get('user')).user

            if user not in group.join_requests.all():
                return HttpResponseForbidden()

            group.join_requests.remove(user)
            push_notification([user], 'group_join_request_rejected',
                              {
                                  'group_name': group.name,
                                  'url': settings.BASE_URL + reverse('group_detail', args=(group.pk,)),
                              })

            return self.render_json_response({
                'member': user.pk,
            })

        # Only AJAX allowed
        return HttpResponseForbidden()
