# Django
from django.conf.urls import patterns, url

from astrobin_apps_platesolving.views.solution import SolutionFinalizeView
from astrobin_apps_platesolving.views.solution import SolutionUpdateView
# This app
from astrobin_apps_platesolving.views.solution import SolveView

urlpatterns = patterns('',
                       url(
                           r'solve/(?P<object_id>\d+)/(?P<content_type_id>\d+)/$',
                           SolveView.as_view(),
                           name='astrobin_apps_platesolution.solve'),

                       url(
                           r'update/(?P<pk>\d+)/$',
                           SolutionUpdateView.as_view(),
                           name='astrobin_apps_platesolution.update'),

                       url(
                           r'finalize/(?P<pk>\d+)/$',
                           SolutionFinalizeView.as_view(),
                           name='astrobin_apps_platesolution.finalize'),
                       )
