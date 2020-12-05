from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'config/', views.stripe_config),
    url(r'create-checkout-session/(?P<product>[\w]*)/$', views.create_checkout_session),
    url(r'stripe-webhook/', views.stripe_webhook),

]

