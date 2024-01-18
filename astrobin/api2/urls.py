from django.conf.urls import url, include
from rest_framework import routers

from astrobin.api2.views.accessory_view_set import AccessoryViewSet
from astrobin.api2.views.camera_rename_proposal_view_set import CameraRenameProposalViewSet
from astrobin.api2.views.camera_view_set import CameraViewSet
from astrobin.api2.views.collection_view_set import CollectionViewSet
from astrobin.api2.views.filter_view_set import FilterViewSet
from astrobin.api2.views.focal_reducer_view_set import FocalReducerViewSet
from astrobin.api2.views.gear_migration_strategy_view_set import GearMigrationStrategyViewSet
from astrobin.api2.views.gear_user_info_view_set import GearUserInfoViewSet
from astrobin.api2.views.gear_view_set import GearViewSet
from astrobin.api2.views.location_view_set import LocationViewSet
from astrobin.api2.views.mount_view_set import MountViewSet
from astrobin.api2.views.software_view_set import SoftwareViewSet
from astrobin.api2.views.telescope_view_set import TelescopeViewSet

router = routers.DefaultRouter()
router.register(r'gear', GearViewSet, basename='gear')
router.register(r'gear-migration-strategy', GearMigrationStrategyViewSet, basename='gear-migration-strategy')
router.register(r'camera', CameraViewSet, basename='camera')
router.register(r'camera-rename-proposal', CameraRenameProposalViewSet, basename='camera-rename-proposal')
router.register(r'telescope', TelescopeViewSet, basename='telescope')
router.register(r'mount', MountViewSet, basename='mount')
router.register(r'filter', FilterViewSet, basename='filter')
router.register(r'accessory', AccessoryViewSet, basename='accessory')
router.register(r'focal-reducer', FocalReducerViewSet, basename='focal-reducer')
router.register(r'software', SoftwareViewSet, basename='software')
router.register(r'gear-user-info', GearUserInfoViewSet, basename='gear-user-info')
router.register(r'location', LocationViewSet, basename='location')
router.register(r'collection', CollectionViewSet, basename='collection')

urlpatterns = [
    url('', include(router.urls)),
]
