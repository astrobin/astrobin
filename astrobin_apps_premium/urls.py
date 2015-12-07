# Django
from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required
from django.views.generic import *

# This app
from astrobin_apps_premium.views import *

urlpatterns = patterns('',
    url(
        r'^cancel/$',
        CancelView.as_view(),
        name = 'astrobin_apps_premium.cancel'),

    url(
        r'^success/$',
        SuccessView.as_view(),
        name = 'astrobin_apps_premium.success'),

    url(
        r'^edit/',
        login_required(EditView.as_view()),
        name = 'astrobin_apps_premium.edit'),

    url(r'^paypal/', include('paypal.standard.ipn.urls')),
)

