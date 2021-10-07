from django.conf.urls import url, include
from rest_framework import routers

from astrobin_apps_equipment.api.views.brand_view_set import BrandViewSet
from astrobin_apps_equipment.api.views.camera_edit_proposal_view_set import CameraEditProposalViewSet
from astrobin_apps_equipment.api.views.camera_view_set import CameraViewSet
from astrobin_apps_equipment.api.views.sensor_view_set import SensorViewSet
from astrobin_apps_equipment.api.views.telescope_edit_proposal_view_set import TelescopeEditProposalViewSet
from astrobin_apps_equipment.api.views.telescope_view_set import TelescopeViewSet

router = routers.DefaultRouter()
router.register(r'brand', BrandViewSet, basename='brand')
router.register(r'sensor', SensorViewSet, basename='sensor')
router.register(r'camera', CameraViewSet, basename='camera')
router.register(r'camera-edit-proposal', CameraEditProposalViewSet, basename='camera-edit-proposal')
router.register(r'telescope', TelescopeViewSet, basename='telescope')
router.register(r'telescope-edit-proposal', TelescopeEditProposalViewSet, basename='telescope-edit-proposal')

urlpatterns = [
    url('', include(router.urls)),
]
