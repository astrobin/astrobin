from django.conf.urls import url, include
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from astrobin_apps_premium.views import *

urlpatterns = (
    url(
        r'^migrate-donations/$',
        login_required(MigrateDonationsView.as_view()),
        name='astrobin_apps_premium.migrate_donations'),
    url(
        r'^migrate-donations/success/$',
        login_required(TemplateView.as_view(template_name="astrobin_apps_premium/migrate_donations_success.html")),
        name='astrobin_apps_premium.migrate_donations_success'),
)
