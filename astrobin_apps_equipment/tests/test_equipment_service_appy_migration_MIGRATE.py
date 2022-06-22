from django.test import TestCase

from astrobin.models import DeepSky_Acquisition
from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models import (
    AccessoryMigrationRecord, CameraMigrationRecord, FilterMigrationRecord, FocalReducerMigrationRecord,
    MigrationUsageType, MountMigrationRecord,
    SoftwareMigrationRecord, TelescopeMigrationRecord,
)
from astrobin_apps_equipment.models.deep_sky_acquisition_migration_record import DeepSkyAcquisitionMigrationRecord
from astrobin_apps_equipment.services import EquipmentService
from astrobin_apps_equipment.tests.equipment_generators import EquipmentGenerators


class EquipmentServiceApplyMigrationMigrateTest(TestCase):
    def test_telescope_imaging(self):
        user = Generators.user()
        image = Generators.image(user=user)
        telescope = Generators.telescope()

        image.imaging_telescopes.add(telescope)

        new_telescope = EquipmentGenerators.telescope()
        migration_strategy = Generators.gear_migration_strategy(
            gear=telescope,
            user=user,
            migration_flag='MIGRATE',
            migration_content_object=new_telescope,
            migration_flat_reviewer_decision='APPROVED'
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertTrue(
            TelescopeMigrationRecord.objects.filter(
                from_gear=telescope, to_item=new_telescope, image=image, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertFalse(image.imaging_telescopes.filter(pk=telescope.pk).exists())
        self.assertTrue(image.imaging_telescopes_2.filter(pk=new_telescope.pk).exists())

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertEquals(
            1,
            TelescopeMigrationRecord.objects.filter(
                from_gear=telescope, to_item=new_telescope, image=image, usage_type=MigrationUsageType.IMAGING
            ).count()
        )
        self.assertFalse(image.imaging_telescopes.filter(pk=telescope.pk).exists())
        self.assertTrue(image.imaging_telescopes_2.filter(pk=new_telescope.pk).exists())

        # Test idempotency

        EquipmentService.undo_migration_strategy(migration_strategy)

        self.assertFalse(
            TelescopeMigrationRecord.objects.filter(
                from_gear=telescope, to_item=new_telescope, image=image, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertTrue(image.imaging_telescopes.filter(pk=telescope.pk).exists())
        self.assertFalse(image.imaging_telescopes_2.filter(pk=new_telescope.pk).exists())

    def test_camera_imaging(self):
        user = Generators.user()
        image = Generators.image(user=user)
        camera = Generators.camera()

        image.imaging_cameras.add(camera)

        new_camera = EquipmentGenerators.camera()
        migration_strategy = Generators.gear_migration_strategy(
            gear=camera,
            user=user,
            migration_flag='MIGRATE',
            migration_content_object=new_camera,
            migration_flat_reviewer_decision='APPROVED'
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertTrue(
            CameraMigrationRecord.objects.filter(
                from_gear=camera, to_item=new_camera, image=image, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertFalse(image.imaging_cameras.filter(pk=camera.pk).exists())
        self.assertTrue(image.imaging_cameras_2.filter(pk=new_camera.pk).exists())

        EquipmentService.undo_migration_strategy(migration_strategy)

        self.assertFalse(
            CameraMigrationRecord.objects.filter(
                from_gear=camera, to_item=new_camera, image=image, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertTrue(image.imaging_cameras.filter(pk=camera.pk).exists())
        self.assertFalse(image.imaging_cameras_2.filter(pk=new_camera.pk).exists())

    def test_telescope_guiding(self):
        user = Generators.user()
        image = Generators.image(user=user)
        telescope = Generators.telescope()

        image.guiding_telescopes.add(telescope)

        new_telescope = EquipmentGenerators.telescope()
        migration_strategy = Generators.gear_migration_strategy(
            gear=telescope,
            user=user,
            migration_flag='MIGRATE',
            migration_content_object=new_telescope,
            migration_flat_reviewer_decision='APPROVED'
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertTrue(
            TelescopeMigrationRecord.objects.filter(
                from_gear=telescope, to_item=new_telescope, image=image, usage_type=MigrationUsageType.GUIDING
            ).exists()
        )
        self.assertFalse(image.guiding_telescopes.filter(pk=telescope.pk).exists())
        self.assertTrue(image.guiding_telescopes_2.filter(pk=new_telescope.pk).exists())

        EquipmentService.undo_migration_strategy(migration_strategy)

        self.assertFalse(
            TelescopeMigrationRecord.objects.filter(
                from_gear=telescope, to_item=new_telescope, image=image, usage_type=MigrationUsageType.GUIDING
            ).exists()
        )
        self.assertTrue(image.guiding_telescopes.filter(pk=telescope.pk).exists())
        self.assertFalse(image.guiding_telescopes_2.filter(pk=new_telescope.pk).exists())

    def test_camera_guiding(self):
        user = Generators.user()
        image = Generators.image(user=user)
        camera = Generators.camera()

        image.guiding_cameras.add(camera)

        new_camera = EquipmentGenerators.camera()
        migration_strategy = Generators.gear_migration_strategy(
            gear=camera,
            user=user,
            migration_flag='MIGRATE',
            migration_content_object=new_camera,
            migration_flat_reviewer_decision='APPROVED'
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertTrue(
            CameraMigrationRecord.objects.filter(
                from_gear=camera, to_item=new_camera, image=image, usage_type=MigrationUsageType.GUIDING
            ).exists()
        )
        self.assertFalse(image.guiding_cameras.filter(pk=camera.pk).exists())
        self.assertTrue(image.guiding_cameras_2.filter(pk=new_camera.pk).exists())

        EquipmentService.undo_migration_strategy(migration_strategy)

        self.assertFalse(
            CameraMigrationRecord.objects.filter(
                from_gear=camera, to_item=new_camera, image=image, usage_type=MigrationUsageType.GUIDING
            ).exists()
        )
        self.assertTrue(image.guiding_cameras.filter(pk=camera.pk).exists())
        self.assertFalse(image.guiding_cameras_2.filter(pk=new_camera.pk).exists())

    def test_mount(self):
        user = Generators.user()
        image = Generators.image(user=user)
        mount = Generators.mount()

        image.mounts.add(mount)

        new_mount = EquipmentGenerators.mount()
        migration_strategy = Generators.gear_migration_strategy(
            gear=mount,
            user=user,
            migration_flag='MIGRATE',
            migration_content_object=new_mount,
            migration_flat_reviewer_decision='APPROVED'
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertTrue(
            MountMigrationRecord.objects.filter(
                from_gear=mount, to_item=new_mount, image=image
            ).exists()
        )
        self.assertFalse(image.mounts.filter(pk=mount.pk).exists())
        self.assertTrue(image.mounts_2.filter(pk=new_mount.pk).exists())

        EquipmentService.undo_migration_strategy(migration_strategy)

        self.assertFalse(
            MountMigrationRecord.objects.filter(
                from_gear=mount, to_item=new_mount, image=image
            ).exists()
        )
        self.assertTrue(image.mounts.filter(pk=mount.pk).exists())
        self.assertFalse(image.mounts_2.filter(pk=new_mount.pk).exists())

    def test_filter(self):
        user = Generators.user()
        image = Generators.image(user=user)

        filter_1 = Generators.filter()
        filter_2 = Generators.filter()

        image.filters.add(filter_1)
        image.filters.add(filter_2)

        deep_sky_acquisition_1 = DeepSky_Acquisition.objects.create(
            image=image,
            filter=filter_1,
            duration=300,
            number=10,
        )

        deep_sky_acquisition_2 = DeepSky_Acquisition.objects.create(
            image=image,
            filter=filter_2,
            duration=300,
            number=10,
        )

        new_filter = EquipmentGenerators.filter()

        migration_strategy_1 = Generators.gear_migration_strategy(
            gear=filter_1,
            user=user,
            migration_flag='MIGRATE',
            migration_content_object=new_filter,
            migration_flat_reviewer_decision='APPROVED'
        )

        # In this test scenario, filter_2 was migrated to new_filter by mistake. When undoing it, we will test that
        # only deep_sky_acquisition_2 gets the filters changed.
        migration_strategy_2 = Generators.gear_migration_strategy(
            gear=filter_2,
            user=user,
            migration_flag='MIGRATE',
            migration_content_object=new_filter,
            migration_flat_reviewer_decision='APPROVED'
        )

        EquipmentService.apply_migration_strategy(migration_strategy_2)

        self.assertTrue(
            FilterMigrationRecord.objects.filter(
                from_gear=filter_2, to_item=new_filter, image=image
            ).exists()
        )
        self.assertFalse(image.filters.filter(pk=filter_2.pk).exists())
        self.assertTrue(image.filters_2.filter(pk=new_filter.pk).exists())
        deep_sky_acquisition_2.refresh_from_db()
        self.assertTrue(new_filter, deep_sky_acquisition_2.filter_2)
        self.assertIsNone(deep_sky_acquisition_2.filter)
        self.assertTrue(DeepSkyAcquisitionMigrationRecord.objects.filter(from_gear=filter_2, to_item=new_filter).exists())

        EquipmentService.apply_migration_strategy(migration_strategy_1)

        self.assertTrue(
            FilterMigrationRecord.objects.filter(
                from_gear=filter_1, to_item=new_filter, image=image
            ).exists()
        )
        self.assertFalse(image.filters.filter(pk=filter_1.pk).exists())
        self.assertTrue(image.filters_2.filter(pk=new_filter.pk).exists())
        deep_sky_acquisition_1.refresh_from_db()
        self.assertTrue(new_filter, deep_sky_acquisition_1.filter_2)
        self.assertIsNone(deep_sky_acquisition_1.filter)
        self.assertTrue(
            DeepSkyAcquisitionMigrationRecord.objects.filter(from_gear=filter_1, to_item=new_filter).exists()
        )

        EquipmentService.undo_migration_strategy(migration_strategy_2)

        self.assertFalse(
            FilterMigrationRecord.objects.filter(
                from_gear=filter_2, to_item=new_filter, image=image
            ).exists()
        )
        self.assertTrue(image.filters.filter(pk=filter_2.pk).exists())
        self.assertFalse(image.filters_2.filter(pk=new_filter.pk).exists())
        deep_sky_acquisition_2.refresh_from_db()
        self.assertTrue(filter_2, deep_sky_acquisition_2.filter)
        self.assertIsNone(deep_sky_acquisition_2.filter_2)

        self.assertTrue(
            FilterMigrationRecord.objects.filter(
                from_gear=filter_1, to_item=new_filter, image=image
            ).exists()
        )
        deep_sky_acquisition_1.refresh_from_db()
        self.assertTrue(new_filter, deep_sky_acquisition_1.filter_2)
        self.assertIsNone(deep_sky_acquisition_1.filter)
        self.assertTrue(
            DeepSkyAcquisitionMigrationRecord.objects.filter(from_gear=filter_1, to_item=new_filter).exists()
        )

    def test_accessory(self):
        user = Generators.user()
        image = Generators.image(user=user)
        accessory = Generators.accessory()

        image.accessories.add(accessory)

        new_accessory = EquipmentGenerators.accessory()
        migration_strategy = Generators.gear_migration_strategy(
            gear=accessory,
            user=user,
            migration_flag='MIGRATE',
            migration_content_object=new_accessory,
            migration_flat_reviewer_decision='APPROVED'
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertTrue(
            AccessoryMigrationRecord.objects.filter(
                from_gear=accessory, to_item=new_accessory, image=image
            ).exists()
        )
        self.assertFalse(image.accessories.filter(pk=accessory.pk).exists())
        self.assertTrue(image.accessories_2.filter(pk=new_accessory.pk).exists())

        EquipmentService.undo_migration_strategy(migration_strategy)

        self.assertFalse(
            AccessoryMigrationRecord.objects.filter(
                from_gear=accessory, to_item=new_accessory, image=image
            ).exists()
        )
        self.assertTrue(image.accessories.filter(pk=accessory.pk).exists())
        self.assertFalse(image.accessories_2.filter(pk=new_accessory.pk).exists())

    def test_focal_reducer(self):
        user = Generators.user()
        image = Generators.image(user=user)
        focal_reducer = Generators.focal_reducer()

        image.focal_reducers.add(focal_reducer)

        new_accessory = EquipmentGenerators.accessory()
        migration_strategy = Generators.gear_migration_strategy(
            gear=focal_reducer,
            user=user,
            migration_flag='MIGRATE',
            migration_content_object=new_accessory,
            migration_flat_reviewer_decision='APPROVED'
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertTrue(
            FocalReducerMigrationRecord.objects.filter(
                from_gear=focal_reducer, to_item=new_accessory, image=image
            ).exists()
        )
        self.assertFalse(image.focal_reducers.filter(pk=focal_reducer.pk).exists())
        self.assertTrue(image.accessories_2.filter(pk=new_accessory.pk).exists())

        EquipmentService.undo_migration_strategy(migration_strategy)

        self.assertFalse(
            FocalReducerMigrationRecord.objects.filter(
                from_gear=focal_reducer, to_item=new_accessory, image=image
            ).exists()
        )
        self.assertTrue(image.focal_reducers.filter(pk=focal_reducer.pk).exists())
        self.assertFalse(image.accessories_2.filter(pk=new_accessory.pk).exists())

    def test_software(self):
        user = Generators.user()
        image = Generators.image(user=user)
        software = Generators.software()

        image.software.add(software)

        new_software = EquipmentGenerators.software()
        migration_strategy = Generators.gear_migration_strategy(
            gear=software,
            user=user,
            migration_flag='MIGRATE',
            migration_content_object=new_software,
            migration_flat_reviewer_decision='APPROVED'
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertTrue(
            SoftwareMigrationRecord.objects.filter(
                from_gear=software, to_item=new_software, image=image
            ).exists()
        )
        self.assertFalse(image.software.filter(pk=software.pk).exists())
        self.assertTrue(image.software_2.filter(pk=new_software.pk).exists())

        EquipmentService.undo_migration_strategy(migration_strategy)

        self.assertFalse(
            SoftwareMigrationRecord.objects.filter(
                from_gear=software, to_item=new_software, image=image
            ).exists()
        )
        self.assertTrue(image.software.filter(pk=software.pk).exists())
        self.assertFalse(image.software_2.filter(pk=new_software.pk).exists())
