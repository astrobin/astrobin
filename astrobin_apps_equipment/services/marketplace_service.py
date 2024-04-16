import logging
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceListing, EquipmentItemMarketplaceOffer,
)
from astrobin_apps_equipment.models.equipment_item_marketplace_offer import EquipmentItemMarketplaceOfferStatus
from astrobin_apps_notifications.utils import build_notification_url
from common.services import AppRedirectionService, DateTimeService

log = logging.getLogger(__name__)


class MarketplaceService:
    @staticmethod
    def offer_notification_params(
            listing: EquipmentItemMarketplaceListing,
            buyer: User,
            offer: Optional[EquipmentItemMarketplaceOffer] = None
    ):
        return {
            'offer': offer,
            'offers': EquipmentItemMarketplaceOffer.objects.filter(
                listing=listing,
                user=buyer,
                status=EquipmentItemMarketplaceOfferStatus.PENDING.value
            ),
            'seller_display_name': listing.user.userprofile.get_display_name(),
            'buyer_display_name': buyer.userprofile.get_display_name(),
            'buyer_url': build_notification_url(
                settings.BASE_URL + reverse('user_page', args=(buyer.username,))
            ),
            'listing': listing,
            'listing_url': build_notification_url(
                AppRedirectionService.redirect(
                    f'/equipment/marketplace/listing/{listing.hash}'
                )
            )
        }

    @staticmethod
    def accept_offer(offer: EquipmentItemMarketplaceOffer):
        offer.status = EquipmentItemMarketplaceOfferStatus.ACCEPTED.value
        offer.save()

        offer.line_item.sold = DateTimeService.now()
        offer.line_item.sold_to = offer.user
        offer.line_item.save()
