from django.conf.urls import include, url
from rest_framework import routers

from astrobin_apps_payments.api.views import AvailableSubscriptionsView, ExchangeRateViewSet, PricingView

router = routers.DefaultRouter()
router.register(r'exchange-rate', ExchangeRateViewSet, basename='exchange-rate')

urlpatterns = [
    url('', include(router.urls)),
    url(r'pricing/(?P<product>\w+)/(?P<currency>\w+)/$', PricingView.as_view()),
    url(r'available-subscriptions', AvailableSubscriptionsView.as_view()),
]
