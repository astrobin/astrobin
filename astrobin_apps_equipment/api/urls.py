from django.conf.urls import include, url
from rest_framework import routers

from astrobin_apps_equipment.api.views.accessory_edit_proposal_view_set import AccessoryEditProposalViewSet
from astrobin_apps_equipment.api.views.accessory_view_set import AccessoryViewSet
from astrobin_apps_equipment.api.views.brand_view_set import BrandViewSet
from astrobin_apps_equipment.api.views.camera_edit_proposal_view_set import CameraEditProposalViewSet
from astrobin_apps_equipment.api.views.camera_view_set import CameraViewSet
from astrobin_apps_equipment.api.views.equipment_contributors_view_set import EquipmentContributorsViewSet
from astrobin_apps_equipment.api.views.equipment_item_group_view_set import EquipmentItemGroupViewSet
from astrobin_apps_equipment.api.views.equipment_item_marketplace_feedback_view_set import \
    EquipmentItemMarketplaceFeedbackViewSet
from astrobin_apps_equipment.api.views.equipment_item_marketplace_listing_line_item_image_view_set import \
    EquipmentItemMarketplaceListingLineItemImageViewSet
from astrobin_apps_equipment.api.views.equipment_item_marketplace_listing_line_item_offer_view_set import \
    EquipmentItemMarketplaceOfferViewSet
from astrobin_apps_equipment.api.views.equipment_item_marketplace_listing_line_item_view_set import \
    EquipmentItemMarketplaceListingLineItemViewSet
from astrobin_apps_equipment.api.views.equipment_item_marketplace_listing_view_set import \
    EquipmentItemMarketplaceListingViewSet
from astrobin_apps_equipment.api.views.equipment_item_marketplace_private_conversation_view_set import \
    EquipmentItemMarketplacePrivateConversationViewSet
from astrobin_apps_equipment.api.views.equipment_item_marketplace_user_feedback_view_set import \
    EquipmentItemMarketplaceUserFeedbackViewSet
from astrobin_apps_equipment.api.views.equipment_preset_view_set import EquipmentPresetViewSet
from astrobin_apps_equipment.api.views.filter_edit_proposal_view_set import FilterEditProposalViewSet
from astrobin_apps_equipment.api.views.filter_view_set import FilterViewSet
from astrobin_apps_equipment.api.views.mount_edit_proposal_view_set import MountEditProposalViewSet
from astrobin_apps_equipment.api.views.mount_view_set import MountViewSet
from astrobin_apps_equipment.api.views.sensor_edit_proposal_view_set import SensorEditProposalViewSet
from astrobin_apps_equipment.api.views.sensor_view_set import SensorViewSet
from astrobin_apps_equipment.api.views.software_edit_proposal_view_set import SoftwareEditProposalViewSet
from astrobin_apps_equipment.api.views.software_view_set import SoftwareViewSet
from astrobin_apps_equipment.api.views.telescope_edit_proposal_view_set import TelescopeEditProposalViewSet
from astrobin_apps_equipment.api.views.telescope_view_set import TelescopeViewSet

router = routers.DefaultRouter()

router.register(r'brand', BrandViewSet, basename='brand')

router.register(r'sensor', SensorViewSet, basename='sensor')
router.register(r'sensor-edit-proposal', SensorEditProposalViewSet, basename='sensor-edit-proposal')

router.register(r'camera', CameraViewSet, basename='camera')
router.register(r'camera-edit-proposal', CameraEditProposalViewSet, basename='camera-edit-proposal')

router.register(r'telescope', TelescopeViewSet, basename='telescope')
router.register(r'telescope-edit-proposal', TelescopeEditProposalViewSet, basename='telescope-edit-proposal')

router.register(r'mount', MountViewSet, basename='mount')
router.register(r'mount-edit-proposal', MountEditProposalViewSet, basename='mount-edit-proposal')

router.register(r'filter', FilterViewSet, basename='filter')
router.register(r'filter-edit-proposal', FilterEditProposalViewSet, basename='filter-edit-proposal')

router.register(r'accessory', AccessoryViewSet, basename='accessory')
router.register(r'accessory-edit-proposal', AccessoryEditProposalViewSet, basename='accessory-edit-proposal')

router.register(r'software', SoftwareViewSet, basename='software')
router.register(r'software-edit-proposal', SoftwareEditProposalViewSet, basename='software-edit-proposal')

router.register(r'equipment-item-group', EquipmentItemGroupViewSet, basename='equipment-item-group')

router.register(r'equipment-preset', EquipmentPresetViewSet, basename='equipment-preset')

router.register(
    r'marketplace/listing',
    EquipmentItemMarketplaceListingViewSet,
    basename='marketplace-listing'
)

router.register(
    r'marketplace/listing/(?P<listing_id>[^/.]+)/line-item',
    EquipmentItemMarketplaceListingLineItemViewSet,
    basename='marketplace-line-item'
)

router.register(
    r'marketplace/listing/(?P<listing_id>[^/.]+)/line-item/(?P<line_item_id>[^/.]+)/image',
    EquipmentItemMarketplaceListingLineItemImageViewSet,
    basename='marketplace-image'
)

router.register(
    r'marketplace/listing/(?P<listing_id>[^/.]+)/line-item/(?P<line_item_id>[^/.]+)/offer',
    EquipmentItemMarketplaceOfferViewSet,
    basename='marketplace-offer'
)

router.register(
    r'marketplace/listing/(?P<listing_id>[^/.]+)/private-conversation',
    EquipmentItemMarketplacePrivateConversationViewSet,
    basename='marketplace-private-conversation'
)

router.register(
    r'marketplace/listing/(?P<listing_id>[^/.]+)/feedback',
    EquipmentItemMarketplaceFeedbackViewSet,
    basename='marketplace-feedback'
)

router.register(
    r'marketplace/user/(?P<user_id>[^/.]+)/feedback',
    EquipmentItemMarketplaceUserFeedbackViewSet,
    basename='marketplace-user-feedback'
)

router.register(
    r'marketplace/feedback',
    EquipmentItemMarketplaceFeedbackViewSet,
    basename='marketplace-user-feedback'
)

urlpatterns = [
    url('', include(router.urls)),
    url(r'contributors/$', EquipmentContributorsViewSet.as_view())
]
