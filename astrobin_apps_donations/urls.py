from django.conf.urls import url, include
from django.contrib.auth.decorators import login_required

from astrobin_apps_donations.views import CancelView, SuccessView, EditView, DonateView

urlpatterns = (
    url(
        r'^donate/',
        login_required(DonateView.as_view()),
        name='astrobin_apps_donations.donate'),

    url(
        r'^cancel/$',
        CancelView.as_view(),
        name='astrobin_apps_donations.cancel'),

    url(
        r'^success/$',
        SuccessView.as_view(),
        name='astrobin_apps_donations.success'),

    url(
        r'^edit/',
        login_required(EditView.as_view()),
        name='astrobin_apps_donations.edit'),

    url(
        r'^paypal/',
        include('paypal.standard.ipn.urls')),
)
