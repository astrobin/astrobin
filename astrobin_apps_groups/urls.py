# Django
from django.conf.urls import patterns, url

# This app
from astrobin_apps_groups.views import *


urlpatterns = patterns('',
    url(
        r'^$',
        PublicGroupListView.as_view(),
        name = 'public_group_list'),
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
        r'^(?P<pk>\d+)/join/$',
        GroupJoinView.as_view(),
        name = 'group_join'),
)
