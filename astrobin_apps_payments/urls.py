from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'config/', views.stripe_config),
    url(
        r'create-checkout-session/'
        r'(?P<user_pk>\d+)/'
        r'(?P<product>[\w]*)/'
        r'(?P<currency>[\w]*)/'
        r'(?P<recurring_unit>[\w]*)/'
        r'(?P<autorenew>[\w]*)/$',
        views.create_checkout_session
    ),
    url(r'stripe-webhook/', views.stripe_webhook),
]

