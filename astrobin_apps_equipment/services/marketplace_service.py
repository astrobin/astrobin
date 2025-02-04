import logging
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from geopy import Nominatim
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from rest_framework.renderers import JSONRenderer
from safedelete.config import FIELD_NAME as DELETED_FIELD_NAME

from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceFeedback, EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem,
    EquipmentItemMarketplaceOffer,
)
from astrobin_apps_equipment.models.equipment_item_marketplace_offer import EquipmentItemMarketplaceOfferStatus
from astrobin_apps_equipment.types.marketplace_feedback import MarketplaceFeedback
from astrobin_apps_equipment.types.marketplace_feedback_target_type import MarketplaceFeedbackTargetType
from astrobin_apps_notifications.services.notifications_service import NotificationContext
from astrobin_apps_notifications.utils import build_notification_url
from astrobin_apps_users.services import UserService
from common.constants import GroupName
from common.services import AppRedirectionService, DateTimeService

log = logging.getLogger(__name__)
marketplace_logger = logging.getLogger("marketplace")

class MarketplaceService:
    @staticmethod
    def offer_notification_params(
            listing: EquipmentItemMarketplaceListing,
            buyer: User,
            master_offer: Optional[EquipmentItemMarketplaceOffer] = None,
            offer: Optional[EquipmentItemMarketplaceOffer] = None
    ):
        return {
            'offer': offer,
            'pending_offers': EquipmentItemMarketplaceOffer.objects.filter(
                listing=listing,
                user=buyer,
                status=EquipmentItemMarketplaceOfferStatus.PENDING.value,
                master_offer=master_offer,
            ) if master_offer else EquipmentItemMarketplaceOffer.objects.none(),
            'accepted_offers': EquipmentItemMarketplaceOffer.objects.filter(
                listing=listing,
                user=buyer,
                status=EquipmentItemMarketplaceOfferStatus.ACCEPTED.value,
                master_offer=master_offer,
            ) if master_offer else EquipmentItemMarketplaceOffer.objects.none(),
            'rejected_offers': EquipmentItemMarketplaceOffer.objects.filter(
                listing=listing,
                user=buyer,
                status=EquipmentItemMarketplaceOfferStatus.REJECTED.value,
                master_offer=master_offer,
            ) if master_offer else EquipmentItemMarketplaceOffer.objects.none(),
            'retracted_offers': EquipmentItemMarketplaceOffer.objects.filter(
                listing=listing,
                user=buyer,
                status=EquipmentItemMarketplaceOfferStatus.RETRACTED.value,
                master_offer=master_offer,
            ) if master_offer else EquipmentItemMarketplaceOffer.objects.none(),
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
            ),
            'extra_tags': {
                'context': NotificationContext.MARKETPLACE
            },
        }

    @staticmethod
    def accept_offer(offer: EquipmentItemMarketplaceOffer):
        offer.status = EquipmentItemMarketplaceOfferStatus.ACCEPTED.value
        offer.save()

        offer.line_item.reserved = DateTimeService.now()
        offer.line_item.reserved_to = offer.user
        offer.line_item.save()

    @staticmethod
    def reject_offer(offer: EquipmentItemMarketplaceOffer):
        offer.status = EquipmentItemMarketplaceOfferStatus.REJECTED.value
        offer.save()

        if offer.line_item.reserved_to == offer.user:
            EquipmentItemMarketplaceListingLineItem.objects.filter(pk=offer.line_item.pk).update(
                reserved=None,
                reserved_to=None
            )

    @staticmethod
    def retract_offer(offer: EquipmentItemMarketplaceOffer):
        offer.status = EquipmentItemMarketplaceOfferStatus.RETRACTED.value
        offer.save()

        if offer.line_item.reserved_to == offer.user:
            EquipmentItemMarketplaceListingLineItem.objects.filter(pk=offer.line_item.pk).update(
                reserved=None,
                reserved_to=None
            )

    @staticmethod
    def calculate_received_feedback_score(user: User) -> Optional[int]:
        score_map = {
            MarketplaceFeedback.POSITIVE.value: 1,
            MarketplaceFeedback.NEUTRAL.value: 0,
            MarketplaceFeedback.NEGATIVE.value: -1,
        }

        buyer_feedback = EquipmentItemMarketplaceFeedback.objects.filter(
            recipient=user,
            target_type=MarketplaceFeedbackTargetType.BUYER.value
        )
        buyer_feedback_count = buyer_feedback.count()

        seller_feedback = EquipmentItemMarketplaceFeedback.objects.filter(
            recipient=user,
            target_type=MarketplaceFeedbackTargetType.SELLER.value
        )
        seller_feedback_count = seller_feedback.count()

        if buyer_feedback_count == 0 and seller_feedback_count == 0:
            return 0

        # Define scores for different feedback types
        seller_scores = {
            'communication': 0,
            'speed': 0,
            'packaging': 0,
            'accuracy': 0,
        }
        buyer_scores = {
            'communication': 0,
            'speed': 0,
        }

        # Aggregate scores by feedback type
        for feedback in buyer_feedback:
            buyer_scores['communication'] += score_map.get(feedback.communication_value, 0)
            buyer_scores['speed'] += score_map.get(feedback.speed_value, 0)
        for feedback in seller_feedback:
            seller_scores['communication'] += score_map.get(feedback.communication_value, 0)
            seller_scores['speed'] += score_map.get(feedback.speed_value, 0)
            seller_scores['packaging'] += score_map.get(feedback.packaging_value, 0)
            seller_scores['accuracy'] += score_map.get(feedback.accuracy_value, 0)

        # Calculate total scores for buyer and seller separately
        buyer_score = (
            sum(buyer_scores.values()) / (2 * buyer_feedback_count)
        ) if buyer_feedback_count > 0 else 0
        seller_score = (
            sum(seller_scores.values()) / (4 * seller_feedback_count)
        ) if seller_feedback_count > 0 else 0

        # Calculate weighted average score based on feedback counts
        total_feedbacks = buyer_feedback_count + seller_feedback_count
        weighted_average_score = (
            (buyer_score * buyer_feedback_count + seller_score * seller_feedback_count) /
            total_feedbacks
        ) if total_feedbacks > 0 else 0

        # Normalize to 0-100 scale
        max_score = 1  # As scores are normalized to not exceed 1
        min_score = -1  # Minimum possible normalized score
        score_range = max_score - min_score
        normalized_score = ((weighted_average_score - min_score) / score_range) * 100

        return int(normalized_score)

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

        EquipmentItemMarketplaceListing.objects.filter(
            pk=listing.pk
        ).update(
            expiration=DateTimeService.now() + timedelta(days=28),
            expired_notification_sent=None
        )

    @staticmethod
    def fill_in_listing_lat_lon(listing: EquipmentItemMarketplaceListing):
        if not listing.city or not listing.country:
            return

        if listing.latitude and listing.longitude:
            return

        geolocator = Nominatim(user_agent="astrobin")
        location = None

        try:
            location = geolocator.geocode(f"{listing.city}, {listing.country}")
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            log.error(f"Error while geocoding {listing.city}, {listing.country}: {str(e)}")

        if location:
            listing.latitude = location.latitude
            listing.longitude = location.longitude


    @staticmethod
    def log_event(user: User, event: str, serializer_class, instance, context=None):
        # Instantiate the serializer with the instance and context
        serialized_instance = serializer_class(instance, context=context)
        serialized_data = serialized_instance.data

        # Render the serialized data to JSON
        json_data = JSONRenderer().render(serialized_data)

        # Log the JSON data
        marketplace_logger.info(
            f"User {user.id}/{user} {event} {instance.__class__.__name__} with data: {json_data.decode('utf-8')}"
        )
