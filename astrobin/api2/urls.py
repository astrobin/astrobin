from django.conf.urls import url, include
from rest_framework import routers

from astrobin.api2.views.accessory_view_set import AccessoryViewSet
from astrobin.api2.views.camera_rename_proposal_view_set import CameraRenameProposalViewSet
from astrobin.api2.views.camera_view_set import CameraViewSet
from astrobin.api2.views.filter_view_set import FilterViewSet
from astrobin.api2.views.gear_view_set import GearViewSet
from astrobin.api2.views.location_view_set import LocationViewSet
from astrobin.api2.views.mount_view_set import MountViewSet
from astrobin.api2.views.software_view_set import SoftwareViewSet
from astrobin.api2.views.telescope_view_set import TelescopeViewSet

router = routers.DefaultRouter()
router.register(r'gear', GearViewSet, basename='gear')
router.register(r'camera', CameraViewSet, basename='camera')
router.register(r'camera-rename-proposal', CameraRenameProposalViewSet, basename='camera-rename-proposal')
router.register(r'telescope', TelescopeViewSet, basename='telescope')
router.register(r'mount', MountViewSet, basename='mount')
router.register(r'filter', FilterViewSet, basename='filter')
router.register(r'accessory', AccessoryViewSet, basename='accessory')
router.register(r'software', SoftwareViewSet, basename='softwarek')
router.register(r'location', LocationViewSet, basename='location')

urlpatterns = [
    url('', include(router.urls)),
]
