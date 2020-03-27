from django.conf.urls import url

from astrobin_apps_groups.views.group_add_image import GroupAddImage
from astrobin_apps_groups.views.group_add_moderator import GroupAddModerator
from astrobin_apps_groups.views.group_add_remove_images import GroupAddRemoveImages
from astrobin_apps_groups.views.group_approve_join_request import GroupApproveJoinRequestView
from astrobin_apps_groups.views.group_create import GroupCreateView
from astrobin_apps_groups.views.group_delete import GroupDeleteView
from astrobin_apps_groups.views.group_detail import GroupDetailView
from astrobin_apps_groups.views.group_invite import GroupInviteView
from astrobin_apps_groups.views.group_join import GroupJoinView
from astrobin_apps_groups.views.group_leave import GroupLeaveView
from astrobin_apps_groups.views.group_list import GroupListView
from astrobin_apps_groups.views.group_manage_members import GroupManageMembersView
from astrobin_apps_groups.views.group_members_list import GroupMembersListView
from astrobin_apps_groups.views.group_moderate_join_requests import GroupModerateJoinRequestsView
from astrobin_apps_groups.views.group_reject_join_request import GroupRejectJoinRequestView
from astrobin_apps_groups.views.group_remove_member import GroupRemoveMember
from astrobin_apps_groups.views.group_remove_moderator import GroupRemoveModerator
from astrobin_apps_groups.views.group_revoke_invitation import GroupRevokeInvitationView
from astrobin_apps_groups.views.group_update import GroupUpdateView

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
