import logging
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from safedelete.config import FIELD_NAME as DELETED_FIELD_NAME

from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceFeedback, EquipmentItemMarketplaceListing, EquipmentItemMarketplaceOffer,
)
from astrobin_apps_equipment.models.equipment_item_marketplace_offer import EquipmentItemMarketplaceOfferStatus
from astrobin_apps_equipment.types.marketplace_feedback import MarketplaceFeedback
from astrobin_apps_notifications.utils import build_notification_url
from astrobin_apps_users.services import UserService
from common.constants import GroupName
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

        offer.line_item.reserved = DateTimeService.now()
        offer.line_item.reserved_to = offer.user
        offer.line_item.save()

    @staticmethod
    def calculate_received_feedback_score(user: User) -> Optional[int]:
        score_map = {
            MarketplaceFeedback.POSITIVE.value: 1,
            MarketplaceFeedback.NEUTRAL.value: 0,
            MarketplaceFeedback.NEGATIVE.value: -1,
        }

        feedbacks = EquipmentItemMarketplaceFeedback.objects.filter(recipient=user)

        total_score = sum(score_map[feedback.value] for feedback in feedbacks)

        # Normalize the score to a 0-100 scale
        max_score = len(feedbacks)  # Maximum possible score
        min_score = -len(feedbacks)  # Minimum possible score
        score_range = max_score - min_score
        normalized_score = ((total_score - min_score) / score_range) * 100 if score_range else 0

        return normalized_score

    @staticmethod
    def received_feedback_count(user: User) -> int:
        return EquipmentItemMarketplaceFeedback.objects.filter(recipient=user).count()

    @staticmethod
    def approve_listing(listing: EquipmentItemMarketplaceListing, moderator: User):
        if not UserService(moderator).is_in_group(GroupName.MARKETPLACE_MODERATORS):
            raise PermissionDenied("Only marketplace moderators can approve listings")

        if getattr(listing, DELETED_FIELD_NAME, None):
            raise PermissionDenied("Cannot approve a deleted listing")

        now = DateTimeService.now()

        listing.approved = now
        listing.approved_by = moderator

        if listing.first_approved is None:
            listing.first_approved = now

        listing.save()

    @staticmethod
    def renew_listing(listing: EquipmentItemMarketplaceListing, user: User):
        if getattr(listing, DELETED_FIELD_NAME, None):
            raise PermissionDenied("Cannot renew a deleted listing")

        if listing.expiration is None:
            raise PermissionDenied("Cannot renew a listing that has no expiration date set")

        if listing.expiration > DateTimeService.now():
            raise PermissionDenied("Cannot renew a listing that has not expired yet")

        if listing.user != user:
            raise PermissionDenied("Cannot renew a listing that does not belong to you")

        listing.expiration = DateTimeService.now() + timedelta(days=7)
        listing.expired_notification_sent = None
        listing.save()