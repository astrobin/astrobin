from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_users.api.views.user_locations_view_set import UserLocationsViewSet

router = routers.DefaultRouter()
router.register(r'locations', UserLocationsViewSet, base_name='locations')

urlpatterns = [
    url('', include(router.urls)),
]
