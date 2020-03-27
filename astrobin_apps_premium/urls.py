from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from astrobin_apps_premium.views import MigrateDonationsView, DataLossCompensationRequestView

urlpatterns = (
    url(
        r'^migrate-donations/$',
        login_required(MigrateDonationsView.as_view()),
        name='astrobin_apps_premium.migrate_donations'),
    url(
        r'^migrate-donations/success/$',
        login_required(TemplateView.as_view(template_name="astrobin_apps_premium/migrate_donations_success.html")),
        name='astrobin_apps_premium.migrate_donations_success'),
    url(
        r'^data-loss-compensation-request/$',
        login_required(DataLossCompensationRequestView.as_view()),
        name='astrobin_apps_premium.data_loss_compensation_request'),
    url(
        r'^data-loss-compensation-request/not-eligible/$',
        login_required(
            TemplateView.as_view(
                template_name="astrobin_apps_premium/data_loss_compensation_request_not_eligible.html")),
        name='astrobin_apps_premium.data_loss_compensation_request_not_eligible'),
    url(
        r'^data-loss-compensation-request/already-done/$',
        login_required(
            TemplateView.as_view(
                template_name="astrobin_apps_premium/data_loss_compensation_request_already_done.html")),
        name='astrobin_apps_premium.data_loss_compensation_request_already_done'),
    url(
        r'^data-loss-compensation-request/success/$',
        login_required(
            TemplateView.as_view(template_name="astrobin_apps_premium/data_loss_compensation_request_success.html")),
        name='astrobin_apps_premium.data_loss_compensation_request_success'),
)
