from django.conf.urls import url, include
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from astrobin_apps_donations.views import CancelView, SuccessView, EditView, DonateView

urlpatterns = (
    url(
        r'^donate/',
        never_cache(login_required(DonateView.as_view())),
        name='astrobin_apps_donations.donate'),

    url(
        r'^cancel/$',
        never_cache(CancelView.as_view()),
        name='astrobin_apps_donations.cancel'),

    url(
        r'^success/$',
        never_cache(SuccessView.as_view()),
        name='astrobin_apps_donations.success'),

    url(
        r'^edit/',
        never_cache(login_required(EditView.as_view())),
        name='astrobin_apps_donations.edit'),

    url(
        r'^paypal/',
        include('paypal.standard.ipn.urls')),
)
