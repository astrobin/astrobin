# Django
from django.conf.urls import patterns, url, include
from django.views.generic import *

# This app
from astrobin_apps_platesolving.views.solution import SolveView
from astrobin_apps_platesolving.views.solution import SolutionUpdateView
from astrobin_apps_platesolving.views.solution import SolutionFinalizeView

urlpatterns = patterns('',
    url(
        r'solve/(?P<object_id>\d+)/(?P<content_type_id>\d+)/$',
        SolveView.as_view(),
        name = 'astrobin_apps_platesolution.solve'),

    url(
        r'update/(?P<pk>\d+)/$',
        SolutionUpdateView.as_view(),
        name = 'astrobin_apps_platesolution.update'),

    url(
        r'finalize/(?P<pk>\d+)/$',
        SolutionFinalizeView.as_view(),
        name = 'astrobin_apps_platesolution.finalize'),
)

