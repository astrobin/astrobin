from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_equipment.api.views.brand_view_set import BrandViewSet
from astrobin_apps_equipment.api.views.camera_view_set import CameraViewSet
from astrobin_apps_equipment.api.views.sensor_view_set import SensorViewSet

router = routers.DefaultRouter()
router.register(r'brand', BrandViewSet, basename='brand')
router.register(r'sensor', SensorViewSet, basename='sensor')
router.register(r'camera', CameraViewSet, basename='camera')

urlpatterns = [
    url('', include(router.urls)),
]
