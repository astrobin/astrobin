from django.conf.urls import url
from views import LandingView

urlpatterns = [
    url(r'^$', LandingView.as_view(), name="main"),
]
