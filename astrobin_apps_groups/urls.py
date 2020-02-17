from django.conf.urls import url

from astrobin_apps_groups.views import GroupListView, GroupCreateView, GroupDetailView, GroupUpdateView, \
    GroupDeleteView, GroupJoinView, GroupLeaveView, GroupManageMembersView, GroupInviteView, GroupAddRemoveImages, \
    GroupRevokeInvitationView, GroupAddImage, GroupAddModerator, GroupRemoveModerator, GroupRemoveMember, \
    GroupMembersListView, GroupModerateJoinRequestsView, GroupApproveJoinRequestView, GroupRejectJoinRequestView

urlpatterns = (
    url(
        r'^$',
        GroupListView.as_view(),
        name='group_list'),
    url(
        r'^create/$',
        GroupCreateView.as_view(),
        name='group_create'),
    url(
        r'^(?P<pk>\d+)/$',
        GroupDetailView.as_view(),
        name='group_detail'),
    url(
        r'^(?P<pk>\d+)/edit/$',
        GroupUpdateView.as_view(),
        name='group_update'),
    url(
        r'^(?P<pk>\d+)/delete/$',
        GroupDeleteView.as_view(),
        name='group_delete'),
    url(
        r'^(?P<pk>\d+)/join/$',
        GroupJoinView.as_view(),
        name='group_join'),
    url(
        r'^(?P<pk>\d+)/leave/$',
        GroupLeaveView.as_view(),
        name='group_leave'),
    url(
        r'^(?P<pk>\d+)/manage-members/$',
        GroupManageMembersView.as_view(),
        name='group_manage_members'),
    url(
        r'^(?P<pk>\d+)/invite/$',
        GroupInviteView.as_view(),
        name='group_invite'),
    url(
        r'^(?P<pk>\d+)/revoke-invitation/$',
        GroupRevokeInvitationView.as_view(),
        name='group_revoke_invitation'),
    url(
        r'^(?P<pk>\d+)/add-remove-images/$',
        GroupAddRemoveImages.as_view(),
        name='group_add_remove_images'),
    url(
        r'^(?P<pk>\d+)/add-image/$',
        GroupAddImage.as_view(),
        name='group_add_image'),
    url(
        r'^(?P<pk>\d+)/add-moderator/$',
        GroupAddModerator.as_view(),
        name='group_add_moderator'),
    url(
        r'^(?P<pk>\d+)/remove-moderator/$',
        GroupRemoveModerator.as_view(),
        name='group_remove_moderator'),
    url(
        r'^(?P<pk>\d+)/remove-member/$',
        GroupRemoveMember.as_view(),
        name='group_remove_member'),
    url(
        r'^(?P<pk>\d+)/members-list/$',
        GroupMembersListView.as_view(),
        name='group_members_list'),
    url(
        r'^(?P<pk>\d+)/moderate-join-requests/$',
        GroupModerateJoinRequestsView.as_view(),
        name='group_moderate_join_requests'),
    url(
        r'^(?P<pk>\d+)/moderate-join-requests/approve/$',
        GroupApproveJoinRequestView.as_view(),
        name='group_approve_join_request'),
    url(
        r'^(?P<pk>\d+)/moderate-join-requests/reject/$',
        GroupRejectJoinRequestView.as_view(),
        name='group_reject_join_request'),
)
