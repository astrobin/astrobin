import mock
from django.contrib.auth.models import User
from django.test import TestCase
from mock import patch

from astrobin.models import GearMigrationStrategy
from astrobin.services.gear_service import GearService
from astrobin.tests.generators import Generators


class GearServiceTest(TestCase):
    def test_has_legacy_gear_false(self):
        image = Generators.image()

        self.assertFalse(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_imaging_telescopes(self):
        image = Generators.image()
        gear_item = Generators.telescope()
        image.imaging_telescopes.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_guiding_telescopes(self):
        image = Generators.image()
        gear_item = Generators.telescope()
        image.guiding_telescopes.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_mounts(self):
        image = Generators.image()
        gear_item = Generators.mount()
        image.mounts.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_imaging_cameras(self):
        image = Generators.image()
        gear_item = Generators.camera()
        image.imaging_cameras.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_guiding_cameras(self):
        image = Generators.image()
        gear_item = Generators.camera()
        image.guiding_cameras.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_focal_reducers(self):
        image = Generators.image()
        gear_item = Generators.focal_reducer()
        image.focal_reducers.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_software(self):
        image = Generators.image()
        gear_item = Generators.software()
        image.software.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_filters(self):
        image = Generators.image()
        gear_item = Generators.filter()
        image.filters.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    def test_has_legacy_gear_accessories(self):
        image = Generators.image()
        gear_item = Generators.accessory()
        image.accessories.add(gear_item)

        self.assertTrue(GearService.image_has_legacy_gear(image))

    @patch("astrobin.services.gear_service.EquipmentService.apply_migration_strategy")
    @patch("astrobin.services.gear_service.push_notification")
    def test_approve_migration_strategy(self, push_notification, apply_migration_strategy):
        moderator: User = Generators.user()
        reviewer: User = Generators.user()
        user: User = Generators.user()
        strategy: GearMigrationStrategy = GearService.approve_migration_strategy(
            Generators.gear_migration_strategy(migration_flag_moderator=moderator, user=user),
            reviewer,
            'reason',
            'comment'
        )

        self.assertEquals(strategy.migration_flag_reviewer, reviewer)
        self.assertEquals(strategy.migration_flag_reviewer_decision, 'APPROVED')
        self.assertIsNone(strategy.migration_flag_reviewer_lock)
        self.assertIsNone(strategy.migration_flag_reviewer_lock_timestamp)
        self.assertIsNone(strategy.gear.migration_flag_moderator_lock)
        self.assertIsNone(strategy.gear.migration_flag_moderator_lock_timestamp)

        self.assertTrue(apply_migration_strategy.called)

        push_notification.assert_has_calls(
            [
                mock.call([user], reviewer, 'equipment-item-migration-approved', mock.ANY),
            ], any_order=True
        )

    @patch("astrobin.services.gear_service.EquipmentService.apply_migration_strategy")
    @patch("astrobin.services.gear_service.push_notification")
    def test_reject_migration_strategy(self, push_notification, apply_migration_strategy):
        moderator: User = Generators.user()
        reviewer: User = Generators.user()
        strategy: GearMigrationStrategy = GearService.reject_migration_strategy(
            Generators.gear_migration_strategy(migration_flag_moderator=moderator),
            reviewer,
            'reason',
            'comment'
        )

        self.assertIsNone(strategy.gear.migration_flag_moderator_lock)
        self.assertIsNone(strategy.gear.migration_flag_moderator_lock_timestamp)
        self.assertFalse(GearMigrationStrategy.objects.filter(pk=strategy.pk).exists())
        self.assertFalse(apply_migration_strategy.called)

        push_notification.assert_has_calls(
            [
                mock.call([moderator], reviewer, 'equipment-item-migration-rejected', mock.ANY),
            ], any_order=True
        )

