# Django
from django.conf.urls import patterns, url

# This app
from astrobin_apps_groups.views import *


urlpatterns = patterns('',
    url(
        r'^/$',
        PublicGroupListView.as_view(),
        name = 'public_group_list'),
)
