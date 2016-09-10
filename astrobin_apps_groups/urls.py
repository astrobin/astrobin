# Django
from django.conf.urls import patterns, url

# This app
from astrobin_apps_groups.views import *


urlpatterns = patterns('',
    url(
        r'^$',
        GroupListView.as_view(),
        name = 'group_list'),
    url(
        r'^create/$',
        GroupCreateView.as_view(),
        name = 'group_create'),
    url(
        r'^(?P<pk>\d+)/$',
        GroupDetailView.as_view(),
        name = 'group_detail'),
    url(
        r'^(?P<pk>\d+)/edit/$',
        GroupUpdateView.as_view(),
        name = 'group_update'),
    url(
        r'^(?P<pk>\d+)/delete/$',
        GroupDeleteView.as_view(),
        name = 'group_delete'),
    url(
        r'^(?P<pk>\d+)/join/$',
        GroupJoinView.as_view(),
        name = 'group_join'),
    url(
        r'^(?P<pk>\d+)/leave/$',
        GroupLeaveView.as_view(),
        name = 'group_leave'),
    url(
        r'^(?P<pk>\d+)/manage-members/$',
        GroupManageMembersView.as_view(),
        name = 'group_manage_members'),
    url(
        r'^(?P<pk>\d+)/invite/$',
        GroupInviteView.as_view(),
        name = 'group_invite'),
    url(
        r'^(?P<pk>\d+)/revoke-invitation/$',
        GroupRevokeInvitationView.as_view(),
        name = 'group_revoke_invitation'),
    url(
        r'^(?P<pk>\d+)/add-remove-images/$',
        GroupAddRemoveImages.as_view(),
        name = 'group_add_remove_images'),
    url(
        r'^(?P<pk>\d+)/add-image/$',
        GroupAddImage.as_view(),
        name = 'group_add_image'),
)
