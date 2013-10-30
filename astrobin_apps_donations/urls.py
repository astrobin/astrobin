# Django
from django.conf.urls.defaults import *
from django.views.generic import *

# This app
from astrobin_apps_donations.views import CancelView, SuccessView

urlpatterns = patterns('',
    url(
        r'^cancel/$',
        CancelView.as_view(),
        name = 'astrobin_apps_donations.cancel'),

    url(
        r'^success/$',
        SuccessView.as_view(),
        name = 'astrobin_apps_donations.success'),

    url(r'^paypal/', include('paypal.standard.ipn.urls')),
)

