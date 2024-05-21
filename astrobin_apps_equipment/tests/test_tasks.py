from datetime import timedelta

from django.test import TestCase
from mock import mock
from mock.mock import patch

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.tasks import notify_about_expired_listings
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators
from common.services import DateTimeService


class TasksTest(TestCase):
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
