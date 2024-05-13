import logging
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceFeedback, EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem,
    EquipmentItemMarketplaceOffer,
)
from astrobin_apps_equipment.models.equipment_item_marketplace_offer import EquipmentItemMarketplaceOfferStatus
from astrobin_apps_equipment.types.marketplace_feedback import MarketplaceFeedback
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

    @staticmethod
    def calculate_received_feedback_score(user: User) -> Optional[int]:
        score_map = {
            MarketplaceFeedback.POSITIVE.value: 1,
            MarketplaceFeedback.NEUTRAL.value: 0,
            MarketplaceFeedback.NEGATIVE.value: -1,
        }

        feedbacks = EquipmentItemMarketplaceFeedback.objects.filter(line_item__user=user)

        total_score = sum(score_map[feedback.value] for feedback in feedbacks)

        # Normalize the score to a 0-100 scale
        max_score = len(feedbacks)  # Maximum possible score
        min_score = -len(feedbacks)  # Minimum possible score
        score_range = max_score - min_score
        normalized_score = ((total_score - min_score) / score_range) * 100 if score_range else 0

        return normalized_score

    @staticmethod
    def received_feedback_count(user: User) -> int:
        return EquipmentItemMarketplaceFeedback.objects.filter(line_item__user=user).count()
