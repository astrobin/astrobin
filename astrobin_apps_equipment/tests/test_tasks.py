from datetime import timedelta

from django.test import TestCase
from mock import mock
from mock.mock import patch

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListingLineItem
from astrobin_apps_equipment.tasks import (
    notify_about_expired_listings, remind_about_marking_items_as_sold,
    remind_about_rating_buyer, remind_about_rating_seller,
)
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators
from astrobin_apps_equipment.types.marketplace_feedback import MarketplaceFeedback
from astrobin_apps_equipment.types.marketplace_feedback_target_type import MarketplaceFeedbackTargetType
from common.services import DateTimeService


class TasksTest(TestCase):
    @patch('astrobin_apps_equipment.tasks.push_notification')
    def test_remind_about_rating_seller_when_there_is_no_feedback(self, push_notification):
        seller = Generators.user()
        buyer = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        EquipmentGenerators.marketplace_line_item(
            user=seller,
            listing=listing,
            reserved=DateTimeService.now() - timedelta(days=11),
            reserved_to=buyer,
            sold=DateTimeService.now() - timedelta(days=11),
            sold_to=buyer,
        )

        remind_about_rating_seller()

        push_notification.assert_called_with(
            [buyer], None, 'marketplace-rate-seller', mock.ANY
        )

    @patch('astrobin_apps_equipment.tasks.push_notification')
    def test_remind_about_rating_seller_when_there_is_seller_feedback(self, push_notification):
        seller = Generators.user()
        buyer = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        EquipmentGenerators.marketplace_line_item(
            user=seller,
            listing=listing,
            reserved=DateTimeService.now() - timedelta(days=11),
            reserved_to=buyer,
            sold=DateTimeService.now() - timedelta(days=11),
            sold_to=buyer,
        )

        EquipmentGenerators.marketplace_feedback(
            user=buyer,
            recipient=seller,
            listing=listing,
            communication_value=MarketplaceFeedback.POSITIVE.value,
            speed_value=MarketplaceFeedback.POSITIVE.value,
            message="Great seller",
            target_type=MarketplaceFeedbackTargetType.SELLER.value
        )

        remind_about_rating_seller()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(
                [buyer], None, 'marketplace-rate-seller', mock.ANY
            )

    @patch('astrobin_apps_equipment.tasks.push_notification')
    def test_remind_about_rating_seller_when_there_is_buyer_feedback(self, push_notification):
        seller = Generators.user()
        buyer = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        EquipmentGenerators.marketplace_line_item(
            user=seller,
            listing=listing,
            reserved=DateTimeService.now() - timedelta(days=11),
            reserved_to=buyer,
            sold=DateTimeService.now() - timedelta(days=11),
            sold_to=buyer,
        )
        EquipmentGenerators.marketplace_feedback(
            user=seller,
            recipient=buyer,
            listing=listing,
            communication_value=MarketplaceFeedback.POSITIVE.value,
            speed_value=MarketplaceFeedback.POSITIVE.value,
            message="Great buyer",
            target_type=MarketplaceFeedbackTargetType.BUYER.value
        )

        remind_about_rating_seller()

        push_notification.assert_called_with(
            [buyer], None, 'marketplace-rate-seller', mock.ANY
        )

    @patch('astrobin_apps_equipment.tasks.push_notification')
    def test_remind_about_rating_buyer_when_there_is_no_feedback(self, push_notification):
        seller = Generators.user()
        buyer = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)

        EquipmentGenerators.marketplace_line_item(
            user=seller,
            listing=listing,
            reserved=DateTimeService.now() - timedelta(days=11),
            reserved_to=buyer,
            sold=DateTimeService.now() - timedelta(days=11),
            sold_to=buyer,
        )

        remind_about_rating_buyer()

        push_notification.assert_called_with(
            [seller], None, 'marketplace-rate-buyer', mock.ANY
        )

    @patch('astrobin_apps_equipment.tasks.push_notification')
    def test_remind_about_rating_buyer_when_there_is_buyer_feedback(self, push_notification):
        seller = Generators.user()
        buyer = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        line_item = EquipmentGenerators.marketplace_line_item(
            user=seller,
            listing=listing,
            reserved=DateTimeService.now() - timedelta(days=11),
            reserved_to=buyer,
            sold=DateTimeService.now() - timedelta(days=11),
            sold_to=buyer,
        )
        EquipmentGenerators.marketplace_feedback(
            user=seller,
            recipient=buyer,
            listing=listing,
            communication_value=MarketplaceFeedback.POSITIVE.value,
            speed_value=MarketplaceFeedback.POSITIVE.value,
            message="Great buyer",
            target_type=MarketplaceFeedbackTargetType.BUYER.value
        )

        remind_about_rating_buyer()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(
                [seller], None, 'marketplace-rate-buyer', mock.ANY
            )

    @patch('astrobin_apps_equipment.tasks.push_notification')
    def test_remind_about_rating_buyer_when_there_is_seller_feedback(self, push_notification):
        seller = Generators.user()
        buyer = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        EquipmentGenerators.marketplace_line_item(
            user=seller,
            listing=listing,
            reserved=DateTimeService.now() - timedelta(days=11),
            reserved_to=buyer,
            sold=DateTimeService.now() - timedelta(days=11),
            sold_to=buyer,
        )
        EquipmentGenerators.marketplace_feedback(
            user=buyer,
            recipient=seller,
            listing=listing,
            communication_value=MarketplaceFeedback.POSITIVE.value,
            speed_value=MarketplaceFeedback.POSITIVE.value,
            message="Great seller",
            target_type=MarketplaceFeedbackTargetType.SELLER.value
        )

        remind_about_rating_buyer()

        push_notification.assert_called_with(
            [seller], None, 'marketplace-rate-buyer', mock.ANY
        )


    @patch('astrobin_apps_equipment.tasks.push_notification')
    def test_notify_about_expired_listings(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        EquipmentGenerators.marketplace_line_item(listing=listing)

        listing.approved = DateTimeService.now()
        listing.approved_by = Generators.user()
        listing.save()

        listing.expiration = DateTimeService.now() - timedelta(hours=1)
        listing.save()

        notify_about_expired_listings()

        push_notification.assert_called_with(
            [seller], None, 'marketplace-listing-expired', mock.ANY
        )

        listing.refresh_from_db()

        self.assertIsNotNone(listing.expired_notification_sent)

    @patch('astrobin_apps_equipment.tasks.push_notification')
    def test_notify_about_expired_listings_if_sold(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        EquipmentGenerators.marketplace_line_item(
            listing=listing,
            sold=DateTimeService.now(),
            sold_to=Generators.user()
        )

        listing.approved = DateTimeService.now()
        listing.approved_by = Generators.user()
        listing.save()

        listing.expiration = DateTimeService.now() - timedelta(hours=1)
        listing.save()

        notify_about_expired_listings()

        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(
                [seller], None, 'marketplace-listing-expired', mock.ANY
            )

        listing.refresh_from_db()

        self.assertIsNone(listing.expired_notification_sent)

    @patch('astrobin_apps_equipment.tasks.push_notification')
    def test_remind_about_marking_items_as_sold(self, push_notification):
        seller = Generators.user()
        listing = EquipmentGenerators.marketplace_listing(user=seller)
        line_item = EquipmentGenerators.marketplace_line_item(
            user=seller,
            listing=listing,
            reserved=DateTimeService.now(),
            reserved_to=Generators.user()
        )

        listing.approved = DateTimeService.now()
        listing.approved_by = Generators.user()
        listing.save()

        remind_about_marking_items_as_sold()

        # Initially the line item is reserved for less than 10 days
        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(
                [seller], None, 'marketplace-mark-sold-reminder', mock.ANY
            )

        line_item.refresh_from_db()

        self.assertIsNone(line_item.mark_as_sold_reminder_sent)

        EquipmentItemMarketplaceListingLineItem.objects.filter(
            pk=line_item.pk
        ).update(
            reserved=DateTimeService.now() - timedelta(days=11)
        )

        remind_about_marking_items_as_sold()

        # Now the line item is reserved for more than 10 days
        push_notification.assert_called_with(
            [seller], None, 'marketplace-mark-sold-reminder', mock.ANY
        )

        push_notification.reset_mock()
        remind_about_marking_items_as_sold()

        # Now the line item ahs already been reminded
        with self.assertRaises(AssertionError):
            push_notification.assert_called_with(
                [seller], None, 'marketplace-mark-sold-reminder', mock.ANY
            )
