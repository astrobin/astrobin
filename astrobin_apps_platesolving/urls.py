# Django
from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required
from django.views.generic import *

# This app
from astrobin_apps_platesolving.views.solution import SolveView

urlpatterns = patterns('',
    url(
        r'solve/(?P<id>\d+)/$',
        login_required(SolveView.as_view()),
        name = 'astrobin_apps_platesolution.solve'),
)

