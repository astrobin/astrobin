from django.conf.urls import url, include
from rest_framework import routers

from astrobin.api2.views.camera_view_set import CameraViewSet
from astrobin.api2.views.location_view_set import LocationViewSet
from astrobin.api2.views.telescope_view_set import TelescopeViewSet

router = routers.DefaultRouter()
router.register(r'telescope', TelescopeViewSet, basename='telescope')
router.register(r'camera', CameraViewSet, basename='camera')
router.register(r'location', LocationViewSet, basename='location')

urlpatterns = [
    url('', include(router.urls)),
]
