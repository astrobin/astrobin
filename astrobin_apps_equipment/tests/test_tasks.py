from datetime import timedelta

from django.test import TestCase
from mock import mock
from mock.mock import patch

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListingLineItem, EquipmentPreset
from astrobin_apps_equipment.tasks import (
    notify_about_expired_listings, remind_about_marking_items_as_sold,
    remind_about_rating_buyer, remind_about_rating_seller, update_equipment_preset_image_count,
    update_equipment_preset_total_integration,
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

    def test_update_equipment_preset_image_count_complete_match(self):
        user = Generators.user()
        telescope = EquipmentGenerators.telescope()
        camera = EquipmentGenerators.camera()
        mount = EquipmentGenerators.mount()

        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )
        preset.imaging_telescopes.add(telescope)
        preset.imaging_cameras.add(camera)
        preset.mounts.add(mount)

        matching_image = Generators.image(user=user)
        matching_image.imaging_telescopes_2.add(telescope)
        matching_image.imaging_cameras_2.add(camera)
        matching_image.mounts_2.add(mount)

        non_matching_image = Generators.image(user=user)

        self.assertIsNone(preset.image_count)
        update_equipment_preset_image_count(preset.pk)
        preset.refresh_from_db()
        self.assertEqual(preset.image_count, 1)

    def test_update_equipment_preset_image_count_partial_match_excluded(self):
        user = Generators.user()
        telescope = EquipmentGenerators.telescope()
        camera = EquipmentGenerators.camera()

        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )
        preset.imaging_telescopes.add(telescope)
        preset.imaging_cameras.add(camera)

        partial_match_image = Generators.image(user=user)
        partial_match_image.imaging_telescopes_2.add(telescope)
        # Missing camera, should not count

        self.assertIsNone(preset.image_count)
        update_equipment_preset_image_count(preset.pk)
        preset.refresh_from_db()
        self.assertEqual(preset.image_count, 0)

    def test_update_equipment_preset_image_count_multiple_matching_images(self):
        user = Generators.user()
        telescope = EquipmentGenerators.telescope()

        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )
        preset.imaging_telescopes.add(telescope)

        # Create 3 matching images
        for _ in range(3):
            image = Generators.image(user=user)
            image.imaging_telescopes_2.add(telescope)

        update_equipment_preset_image_count(preset.pk)
        preset.refresh_from_db()
        self.assertEqual(preset.image_count, 3)

    def test_update_equipment_preset_image_count_different_user_images_excluded(self):
        user = Generators.user()
        other_user = Generators.user()
        telescope = EquipmentGenerators.telescope()

        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )
        preset.imaging_telescopes.add(telescope)

        # Create matching image for different user
        other_user_image = Generators.image(user=other_user)
        other_user_image.imaging_telescopes_2.add(telescope)

        update_equipment_preset_image_count(preset.pk)
        preset.refresh_from_db()
        self.assertEqual(preset.image_count, 0)

    def test_update_equipment_preset_image_count_empty_preset(self):
        user = Generators.user()
        other_user = Generators.user()  # Different user

        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )

        # Create an unrelated image for a different user
        Generators.image(user=other_user)

        update_equipment_preset_image_count(preset.pk)
        preset.refresh_from_db()
        self.assertEqual(preset.image_count, 0)

    def test_update_equipment_preset_image_count_not_found(self):
        # Should not raise an exception
        update_equipment_preset_image_count(99999)

    def test_update_equipment_preset_image_count_multiple_equipment_options(self):
        user = Generators.user()
        telescope1 = EquipmentGenerators.telescope()
        telescope2 = EquipmentGenerators.telescope()
        camera = EquipmentGenerators.camera()

        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )
        preset.imaging_telescopes.add(telescope1, telescope2)
        preset.imaging_cameras.add(camera)

        # Image matching first telescope
        image1 = Generators.image(user=user)
        image1.imaging_telescopes_2.add(telescope1)
        image1.imaging_cameras_2.add(camera)

        # Image matching second telescope
        image2 = Generators.image(user=user)
        image2.imaging_telescopes_2.add(telescope2)
        image2.imaging_cameras_2.add(camera)

        update_equipment_preset_image_count(preset.pk)
        preset.refresh_from_db()
        self.assertEqual(preset.image_count, 2)

    def test_update_equipment_preset_total_integration(self):
        user = Generators.user()
        telescope = EquipmentGenerators.telescope()
        camera = EquipmentGenerators.camera()
        mount = EquipmentGenerators.mount()

        preset = EquipmentPreset.objects.create(
            user=user,
            name="Test",
        )
        preset.imaging_telescopes.add(telescope)
        preset.imaging_cameras.add(camera)
        preset.mounts.add(mount)

        matching_image = Generators.image(user=user)
        matching_image.imaging_telescopes_2.add(telescope)
        matching_image.imaging_cameras_2.add(camera)
        matching_image.mounts_2.add(mount)
        matching_image.save()

        Generators.deep_sky_acquisition(image=matching_image, number=60, duration=60)

        self.assertIsNone(preset.total_integration)
        update_equipment_preset_total_integration(preset.pk)
        preset.refresh_from_db()
        self.assertEqual(preset.total_integration, 3600)


def test_update_equipment_preset_total_integration_multiple_acquisitions(self):
    user = Generators.user()
    telescope = EquipmentGenerators.telescope()
    camera = EquipmentGenerators.camera()

    preset = EquipmentPreset.objects.create(
        user=user,
        name="Test",
    )
    preset.imaging_telescopes.add(telescope)
    preset.imaging_cameras.add(camera)

    matching_image = Generators.image(user=user)
    matching_image.imaging_telescopes_2.add(telescope)
    matching_image.imaging_cameras_2.add(camera)
    matching_image.save()

    # Multiple acquisitions for the same image
    Generators.deep_sky_acquisition(image=matching_image, number=30, duration=60)  # 1800s
    Generators.deep_sky_acquisition(image=matching_image, number=20, duration=120)  # 2400s

    update_equipment_preset_total_integration(preset.pk)
    preset.refresh_from_db()
    self.assertEqual(preset.total_integration, 4200)  # 1800 + 2400


def test_update_equipment_preset_total_integration_multiple_images(self):
    user = Generators.user()
    telescope = EquipmentGenerators.telescope()

    preset = EquipmentPreset.objects.create(
        user=user,
        name="Test",
    )
    preset.imaging_telescopes.add(telescope)

    # First image
    image1 = Generators.image(user=user)
    image1.imaging_telescopes_2.add(telescope)
    image1.save()
    Generators.deep_sky_acquisition(image=image1, number=10, duration=60)  # 600s

    # Second image
    image2 = Generators.image(user=user)
    image2.imaging_telescopes_2.add(telescope)
    image2.save()
    Generators.deep_sky_acquisition(image=image2, number=5, duration=120)  # 600s

    update_equipment_preset_total_integration(preset.pk)
    preset.refresh_from_db()
    self.assertEqual(preset.total_integration, 1200)  # 600 + 600


def test_update_equipment_preset_total_integration_no_acquisition_data(self):
    user = Generators.user()
    telescope = EquipmentGenerators.telescope()

    preset = EquipmentPreset.objects.create(
        user=user,
        name="Test",
    )
    preset.imaging_telescopes.add(telescope)

    matching_image = Generators.image(user=user)
    matching_image.imaging_telescopes_2.add(telescope)
    matching_image.save()
    # No acquisition data created

    update_equipment_preset_total_integration(preset.pk)
    preset.refresh_from_db()
    self.assertEqual(preset.total_integration, 0)


def test_update_equipment_preset_total_integration_partial_match_excluded(self):
    user = Generators.user()
    telescope = EquipmentGenerators.telescope()
    camera = EquipmentGenerators.camera()

    preset = EquipmentPreset.objects.create(
        user=user,
        name="Test",
    )
    preset.imaging_telescopes.add(telescope)
    preset.imaging_cameras.add(camera)

    # Image only matches telescope, not camera
    partial_match_image = Generators.image(user=user)
    partial_match_image.imaging_telescopes_2.add(telescope)
    partial_match_image.save()
    Generators.deep_sky_acquisition(image=partial_match_image, number=10, duration=60)

    update_equipment_preset_total_integration(preset.pk)
    preset.refresh_from_db()
    self.assertEqual(preset.total_integration, 0)


def test_update_equipment_preset_total_integration_different_user_excluded(self):
    user = Generators.user()
    other_user = Generators.user()
    telescope = EquipmentGenerators.telescope()

    preset = EquipmentPreset.objects.create(
        user=user,
        name="Test",
    )
    preset.imaging_telescopes.add(telescope)

    # Create matching image for different user
    other_user_image = Generators.image(user=other_user)
    other_user_image.imaging_telescopes_2.add(telescope)
    other_user_image.save()
    Generators.deep_sky_acquisition(image=other_user_image, number=10, duration=60)

    update_equipment_preset_total_integration(preset.pk)
    preset.refresh_from_db()
    self.assertEqual(preset.total_integration, 0)


def test_update_equipment_preset_total_integration_empty_preset(self):
    user = Generators.user()
    preset = EquipmentPreset.objects.create(
        user=user,
        name="Test",
    )

    image = Generators.image(user=user)
    image.save()
    Generators.deep_sky_acquisition(image=image, number=10, duration=60)

    update_equipment_preset_total_integration(preset.pk)
    preset.refresh_from_db()
    self.assertEqual(preset.total_integration, 0)


def test_update_equipment_preset_total_integration_not_found(self):
    # Should not raise an exception
    update_equipment_preset_total_integration(99999)


def test_update_equipment_preset_total_integration_zero_duration(self):
    user = Generators.user()
    telescope = EquipmentGenerators.telescope()

    preset = EquipmentPreset.objects.create(
        user=user,
        name="Test",
    )
    preset.imaging_telescopes.add(telescope)

    matching_image = Generators.image(user=user)
    matching_image.imaging_telescopes_2.add(telescope)
    matching_image.save()
    Generators.deep_sky_acquisition(image=matching_image, number=10, duration=0)

    update_equipment_preset_total_integration(preset.pk)
    preset.refresh_from_db()
    self.assertEqual(preset.total_integration, 0)


def test_update_equipment_preset_total_integration_mixed_durations(self):
    user = Generators.user()
    telescope = EquipmentGenerators.telescope()

    preset = EquipmentPreset.objects.create(
        user=user,
        name="Test",
    )
    preset.imaging_telescopes.add(telescope)

    # Image 1 with multiple acquisitions
    image1 = Generators.image(user=user)
    image1.imaging_telescopes_2.add(telescope)
    image1.save()
    Generators.deep_sky_acquisition(image=image1, number=10, duration=60)  # 600s
    Generators.deep_sky_acquisition(image=image1, number=0, duration=60)  # 0s
    Generators.deep_sky_acquisition(image=image1, number=5, duration=0)  # 0s

    # Image 2 with valid acquisition
    image2 = Generators.image(user=user)
    image2.imaging_telescopes_2.add(telescope)
    image2.save()
    Generators.deep_sky_acquisition(image=image2, number=5, duration=120)  # 600s

    update_equipment_preset_total_integration(preset.pk)
    preset.refresh_from_db()
    self.assertEqual(preset.total_integration, 1200)  # 600 + 600
