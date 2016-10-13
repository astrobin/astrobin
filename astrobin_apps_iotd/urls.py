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
    url(
        r'^submission-queue/$',
        IotdSubmissionQueueView.as_view(),
        name = 'iotd_submission_queue'),
    url(
        r'^toggle-vote-ajax/(?P<pk>\d+)/$',
        IotdToggleVoteAjaxView.as_view(),
        name = 'iotd_toggle_vote_ajax'),
)
