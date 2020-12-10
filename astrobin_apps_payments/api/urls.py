from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_payments.api.views.exchange_rate_view_set import ExchangeRateViewSet
from astrobin_apps_payments.api.views.pricing_view import PricingView

router = routers.DefaultRouter()
router.register(r'exchange-rate', ExchangeRateViewSet, base_name='exchange-rate')

urlpatterns = [
    url('', include(router.urls)),
    url(r'pricing/(?P<product>\w+)/(?P<currency>\w+)/$', PricingView.as_view())
]
