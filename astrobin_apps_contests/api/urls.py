from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_contests.api.views import ContestViewSet

router = routers.DefaultRouter()
router.register(r'contest', ContestViewSet, base_name='contest')

urlpatterns = [
    url('', include(router.urls)),
]
