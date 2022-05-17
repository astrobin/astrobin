from django.test import TestCase

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models import (
    AccessoryMigrationRecord, CameraMigrationRecord, FilterMigrationRecord, FocalReducerMigrationRecord,
    MigrationUsageType, MountMigrationRecord,
    SoftwareMigrationRecord, TelescopeMigrationRecord,
)
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

    def test_camera_imaging(self):
        user = Generators.user()
        image = Generators.image(user=user)
        camera = Generators.camera()

        image.imaging_cameras.add(camera)

        new_camera = EquipmentGenerators.camera()
        migration_strategy = Generators.gear_migration_strategy(
            gear=camera,
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

    def test_telescope_guiding(self):
        user = Generators.user()
        image = Generators.image(user=user)
        telescope = Generators.telescope()

        image.guiding_telescopes.add(telescope)

        new_telescope = EquipmentGenerators.telescope()
        migration_strategy = Generators.gear_migration_strategy(
            gear=telescope,
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

    def test_camera_guiding(self):
        user = Generators.user()
        image = Generators.image(user=user)
        camera = Generators.camera()

        image.guiding_cameras.add(camera)

        new_camera = EquipmentGenerators.camera()
        migration_strategy = Generators.gear_migration_strategy(
            gear=camera,
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

    def test_mount(self):
        user = Generators.user()
        image = Generators.image(user=user)
        mount = Generators.mount()

        image.mounts.add(mount)

        new_mount = EquipmentGenerators.mount()
        migration_strategy = Generators.gear_migration_strategy(
            gear=mount,
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

    def test_filter(self):
        user = Generators.user()
        image = Generators.image(user=user)
        filter = Generators.filter()

        image.filters.add(filter)

        new_filter = EquipmentGenerators.filter()
        migration_strategy = Generators.gear_migration_strategy(
            gear=filter,
            migration_flag='MIGRATE',
            migration_content_object=new_filter,
            migration_flat_reviewer_decision='APPROVED'
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertTrue(
            FilterMigrationRecord.objects.filter(
                from_gear=filter, to_item=new_filter, image=image
            ).exists()
        )
        self.assertFalse(image.filters.filter(pk=filter.pk).exists())
        self.assertTrue(image.filters_2.filter(pk=new_filter.pk).exists())

    def test_accessory(self):
        user = Generators.user()
        image = Generators.image(user=user)
        accessory = Generators.accessory()

        image.accessories.add(accessory)

        new_accessory = EquipmentGenerators.accessory()
        migration_strategy = Generators.gear_migration_strategy(
            gear=accessory,
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

    def test_focal_reducer(self):
        user = Generators.user()
        image = Generators.image(user=user)
        focal_reducer = Generators.focal_reducer()

        image.focal_reducers.add(focal_reducer)

        new_accessory = EquipmentGenerators.accessory()
        migration_strategy = Generators.gear_migration_strategy(
            gear=focal_reducer,
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

    def test_software(self):
        user = Generators.user()
        image = Generators.image(user=user)
        software = Generators.software()

        image.software.add(software)

        new_software = EquipmentGenerators.software()
        migration_strategy = Generators.gear_migration_strategy(
            gear=software,
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
