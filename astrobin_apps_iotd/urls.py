# Django
from django.conf.urls import patterns, url

# This app
from astrobin_apps_iotd.views import *


urlpatterns = patterns('',
    url(
        r'^submission/create/$',
        IotdSubmissionCreateView.as_view(),
        name = 'iotd_submission_create'),
    url(
        r'^submission/(?P<pk>\d+)/$',
        IotdSubmissionDetailView.as_view(),
        name = 'iotd_submission_detail'),
)
