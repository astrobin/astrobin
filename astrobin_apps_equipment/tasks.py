import logging
from datetime import datetime, timedelta
from typing import List, Optional

from annoying.functions import get_object_or_None
from celery import shared_task
from django.contrib.auth.models import User
from django.utils import timezone

from astrobin.models import GearMigrationStrategy
from astrobin.services.gear_service import GearService
from astrobin_apps_equipment.models import (
    Accessory, AccessoryEditProposal, Camera, CameraEditProposal, EquipmentItemMarketplaceFeedback,
    EquipmentItemMarketplaceListing,
    EquipmentItemMarketplaceListingLineItem, EquipmentItemMarketplaceMasterOffer, EquipmentItemMarketplaceOffer, Filter,
    FilterEditProposal, Mount,
    MountEditProposal,
    Sensor, SensorEditProposal, Software, SoftwareEditProposal, Telescope,
    TelescopeEditProposal,
)
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.models.equipment_item_marketplace_offer import EquipmentItemMarketplaceOfferStatus
from astrobin_apps_equipment.services import EquipmentService
from astrobin_apps_equipment.services.marketplace_service import MarketplaceService
from astrobin_apps_equipment.services.stock import StockImporterService
from astrobin_apps_equipment.services.stock.plugins.agena import AgenaStockImporterPlugin
from astrobin_apps_equipment.types.marketplace_feedback_target_type import MarketplaceFeedbackTargetType
from astrobin_apps_notifications.utils import build_notification_url, push_notification
from common.services import DateTimeService

log = logging.getLogger(__name__)


@shared_task(time_limit=300)
def expire_equipment_locks():
    expiration_minutes = 30

    for Model in (Telescope, Camera, Sensor, Mount, Filter, Accessory, Software):
        Model.objects.filter(
            reviewer_lock__isnull=False,
            reviewer_lock_timestamp__lt=timezone.now() - timedelta(minutes=expiration_minutes)
        ).update(
            reviewer_lock=None,
            reviewer_lock_timestamp=None
        )
        Model.objects.filter(
            edit_proposal_lock__isnull=False,
            edit_proposal_lock_timestamp__lt=timezone.now() - timedelta(minutes=expiration_minutes)
        ).update(
            edit_proposal_lock=None,
            edit_proposal_lock_timestamp=None
        )

    for Model in (
        TelescopeEditProposal,
        CameraEditProposal,
        SensorEditProposal,
        MountEditProposal,
        FilterEditProposal,
        AccessoryEditProposal,
        SoftwareEditProposal
    ):
        Model.objects.filter(
            edit_proposal_review_lock__isnull=False,
            edit_proposal_review_lock_timestamp__lt=timezone.now() - timedelta(minutes=expiration_minutes)
        ).update(
            edit_proposal_review_lock=None,
            edit_proposal_review_lock_timestamp=None
        )


@shared_task(time_limit=30 * 60, acks_late=True)
def approve_migration_strategy(migration_strategy_id: int, moderator_id: int):
    migration_strategy: GearMigrationStrategy = get_object_or_None(GearMigrationStrategy, id=migration_strategy_id)
    moderator: User = get_object_or_None(User, id=moderator_id)

    if migration_strategy and moderator:
        GearService.approve_migration_strategy(migration_strategy, moderator)


@shared_task(time_limit=30 * 60, acks_late=True)
def reject_item(item_id: int, klass: EquipmentItemKlass):
    ModelClass = {
        EquipmentItemKlass.SENSOR: Sensor,
        EquipmentItemKlass.TELESCOPE: Telescope,
        EquipmentItemKlass.CAMERA: Camera,
        EquipmentItemKlass.MOUNT: Mount,
        EquipmentItemKlass.FILTER: Filter,
        EquipmentItemKlass.ACCESSORY: Accessory,
        EquipmentItemKlass.SOFTWARE: Software
    }.get(klass)

    item: ModelClass = get_object_or_None(ModelClass, id=item_id)

    if item:
        log.debug(f'reject_item task beginning rejection of {klass}/{item_id}')
        EquipmentService.reject_item(item)


@shared_task(time_limit=30*60, acks_late=True)
def reject_stuck_items():
    cutoff = datetime.now() - timedelta(hours=1)

    for model_class in (Sensor, Telescope, Camera, Mount, Filter, Accessory, Software):
        stuck_items = model_class.objects.filter(reviewer_decision='REJECTED', reviewed_timestamp__lt=cutoff)
        for item in stuck_items.iterator():
            log.debug(f'reject_stuck_items task beginning rejection of {model_class}/{item.id}')
            EquipmentService.reject_item(item)


@shared_task(time_limit=300)
def import_stock_feed_agena():
    importer = StockImporterService(AgenaStockImporterPlugin())
    importer.import_stock()


@shared_task(time_limit=300)
def send_offer_notifications(
        listing_id: int,
        buyer_id: int,
        master_offer_id: Optional[int],
        offer_id: Optional[int],
        recipient_ids: List[int],
        sender_id: Optional[int],
        notice_label: str
):
    listing = EquipmentItemMarketplaceListing.objects.get(pk=listing_id)
    buyer = User.objects.get(pk=buyer_id)
    master_offer = EquipmentItemMarketplaceMasterOffer.objects.get(pk=master_offer_id) if master_offer_id else None
    offer = EquipmentItemMarketplaceOffer.objects.get(pk=offer_id) if offer_id else None

    # Integrity check in case the status of the offer has changed since the task was scheduled.
    integrity_check_offer = None
    if master_offer:
        integrity_check_offer = master_offer
    elif offer:
        integrity_check_offer = offer

    if integrity_check_offer:
        if (
            'offer-created' in notice_label
            and integrity_check_offer.status != EquipmentItemMarketplaceOfferStatus.PENDING.value
        ) or (
            'offer-accepted' in notice_label and
            integrity_check_offer.status != EquipmentItemMarketplaceOfferStatus.ACCEPTED.value
        ) or (
            'offer-rejected' in notice_label and
            integrity_check_offer.status != EquipmentItemMarketplaceOfferStatus.REJECTED.value
        ) or (
            'offer-retracted' in notice_label and
            integrity_check_offer.status != EquipmentItemMarketplaceOfferStatus.RETRACTED.value
        ):
            log.warning(
                f"Offer status doesn't match the notice label. Skipping notification. "
                f"Offer status: {integrity_check_offer.status}, notice label: {notice_label}"
            )
            return

    recipients = User.objects.filter(pk__in=recipient_ids)
    if sender_id:
        sender = User.objects.get(pk=sender_id)
    else:
        sender = None

    push_notification(
        list(recipients),
        sender,
        notice_label,
        MarketplaceService.offer_notification_params(listing, buyer, master_offer, offer),
    )


@shared_task(time_limit=300)
def remind_about_rating_seller():
    days = 10
    cutoff = timezone.now() - timezone.timedelta(days=days)

    # Get all sold items without a seller rating reminder
    line_items = EquipmentItemMarketplaceListingLineItem.objects.filter(
        sold__lt=cutoff,
        sold_to__isnull=False,
        listing__rate_seller_reminder_sent__isnull=True
    ).select_related('listing__user__userprofile', 'sold_to')

    # Dictionary to keep track of users we've reminded
    reminded_users = {}

    for line_item in line_items:
        buyer = line_item.sold_to
        listing = line_item.listing

        # Check if we've already reminded this buyer
        if buyer.id in reminded_users:
            continue

        # Check if feedback already exists
        feedback_exists = EquipmentItemMarketplaceFeedback.objects.filter(
            user=buyer,
            target_type=MarketplaceFeedbackTargetType.SELLER.value,
            listing=listing
        ).exists()

        if not feedback_exists:
            push_notification(
                [buyer],
                None,
                'marketplace-rate-seller',
                {
                    'seller_display_name': listing.user.userprofile.get_display_name(),
                    'listing': listing,
                    'listing_url': build_notification_url(listing.get_absolute_url())
                }
            )

            listing.rate_seller_reminder_sent = timezone.now()
            listing.save(update_fields=['rate_seller_reminder_sent'])

            reminded_users[buyer.id] = True


@shared_task(time_limit=300)
def remind_about_rating_buyer():
    days = 10
    cutoff = timezone.now() - timezone.timedelta(days=days)

    # Get all sold items without a buyer rating reminder
    line_items = EquipmentItemMarketplaceListingLineItem.objects.filter(
        sold__lt=cutoff,
        sold_to__isnull=False,
        listing__rate_buyer_reminder_sent__isnull=True
    ).select_related('listing__user__userprofile', 'user', 'sold_to')

    # Dictionary to keep track of users we've reminded
    reminded_users = {}

    for line_item in line_items:
        seller = line_item.user
        listing = line_item.listing

        # Check if we've already reminded this seller
        if seller.id in reminded_users:
            continue

        # Check if feedback already exists
        feedback_exists = EquipmentItemMarketplaceFeedback.objects.filter(
            user=seller,
            target_type=MarketplaceFeedbackTargetType.BUYER.value,
            listing=listing
        ).exists()

        if not feedback_exists:
            push_notification(
                [seller],
                None,
                'marketplace-rate-buyer',
                {
                    'buyer_display_name': line_item.sold_to.userprofile.get_display_name(),
                    'listing': listing,
                    'listing_url': build_notification_url(listing.get_absolute_url())
                }
            )

            listing.rate_buyer_reminder_sent = timezone.now()
            listing.save(update_fields=['rate_buyer_reminder_sent'])

            reminded_users[seller.id] = True


@shared_task(time_limit=300)
def notify_about_expired_listings():
    # Find all listings that have expired
    listings = EquipmentItemMarketplaceListing.objects.filter(
        expiration__lt=timezone.now(),
        expired_notification_sent__isnull=True
    )

    # Loop all listings and send a reminder to the seller
    for listing in listings:
        # Skip listing in which all line items have been sold
        if listing.line_items.filter(sold__isnull=False).count() == listing.line_items.count():
            continue

        push_notification(
            [listing.user],
            None,
            'marketplace-listing-expired',
            {
                'listing': listing,
                'listing_url': build_notification_url(listing.get_absolute_url())
            }
        )

        EquipmentItemMarketplaceListing.objects.filter(
            pk=listing.pk
        ).update(
            expired_notification_sent=DateTimeService.now()
        )


@shared_task(time_limit=300)
def remind_about_marking_items_as_sold():
    # Find all line items that have been reserved for more than 10 days and have not been marked as sold
    days = 10
    cutoff = datetime.now() - timedelta(days=days)
    line_items = EquipmentItemMarketplaceListingLineItem.objects.filter(
        reserved__lt=cutoff,
        sold__isnull=True,
        mark_as_sold_reminder_sent__isnull=True
    )

    # Keep track of users to avoid sending multiple reminders
    users = set()

    # Loop all line items and send a reminder to the buyer
    for line_item in line_items:
        if line_item.sold_to in users:
            continue

        listing = line_item.listing

        push_notification(
            [line_item.user],
            None,
            'marketplace-mark-sold-reminder',
            {
                'listing': listing,
                'listing_url': build_notification_url(listing.get_absolute_url())
            }
        )

        EquipmentItemMarketplaceListingLineItem.objects.filter(
            pk=line_item.pk
        ).update(
            mark_as_sold_reminder_sent=DateTimeService.now()
        )

        users.add(line_item.sold_to)


@shared_task(time_limit=30)
def auto_approve_marketplace_listings():
    listings = EquipmentItemMarketplaceListing.objects.filter(
        approved__isnull=True,
        manual_approval_required=False,
        expiration__gt=timezone.now(),
        user__userprofile__detected_insecure_password__isnull=True
    )

    admin = User.objects.get(username='astrobin')

    for listing in listings:
        MarketplaceService.approve_listing(listing, admin)
