# Django
from django.conf.urls.defaults import *
from django.views.generic import *

# This app
from astrobin_apps_platesolving.views.solution import SolveView
from astrobin_apps_platesolving.views.solution import SolutionUpdateView

urlpatterns = patterns('',
    url(
        r'solve/(?P<pk>\d+)/$',
        SolveView.as_view(),
        name = 'astrobin_apps_platesolution.solve'),

    url(
        r'update/(?P<pk>\d+)/$',
        SolutionUpdateView.as_view(),
        name = 'astrobin_apps_platesolution.update'),

)

