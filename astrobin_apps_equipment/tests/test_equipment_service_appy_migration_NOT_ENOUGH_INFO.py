from django.test import TestCase

from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models import (
    AccessoryMigrationRecord, CameraMigrationRecord, FilterMigrationRecord, FocalReducerMigrationRecord,
    MountMigrationRecord,
    SoftwareMigrationRecord, TelescopeMigrationRecord,
)
from astrobin_apps_equipment.services import EquipmentService


class EquipmentServiceApplyMigrationMigrateTest(TestCase):
    def test_telescope_imaging(self):
        image = Generators.image()
        telescope = Generators.telescope()

        image.imaging_telescopes.add(telescope)

        migration_strategy = Generators.gear_migration_strategy(
            gear=telescope,
            migration_flag='NOT_ENOUGH_INFO',
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertFalse(TelescopeMigrationRecord.objects.filter(from_gear=telescope, image=image).exists())
        self.assertTrue(image.imaging_telescopes.filter(pk=telescope.pk).exists())

    def test_telescope_guiding(self):
        image = Generators.image()
        telescope = Generators.telescope()

        image.guiding_telescopes.add(telescope)

        migration_strategy = Generators.gear_migration_strategy(
            gear=telescope,
            migration_flag='NOT_ENOUGH_INFO',
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertFalse(TelescopeMigrationRecord.objects.filter(from_gear=telescope, image=image).exists())
        self.assertTrue(image.guiding_telescopes.filter(pk=telescope.pk).exists())

    def test_camera_imaging(self):
        image = Generators.image()
        camera = Generators.camera()

        image.imaging_cameras.add(camera)

        migration_strategy = Generators.gear_migration_strategy(
            gear=camera,
            migration_flag='NOT_ENOUGH_INFO',
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertFalse(CameraMigrationRecord.objects.filter(from_gear=camera, image=image).exists())
        self.assertTrue(image.imaging_cameras.filter(pk=camera.pk).exists())

    def test_camera_guiding(self):
        image = Generators.image()
        camera = Generators.camera()

        image.guiding_cameras.add(camera)

        migration_strategy = Generators.gear_migration_strategy(
            gear=camera,
            migration_flag='NOT_ENOUGH_INFO',
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertFalse(CameraMigrationRecord.objects.filter(from_gear=camera, image=image).exists())
        self.assertTrue(image.guiding_cameras.filter(pk=camera.pk).exists())

    def test_mount(self):
        image = Generators.image()
        mount = Generators.mount()

        image.mounts.add(mount)

        migration_strategy = Generators.gear_migration_strategy(
            gear=mount,
            migration_flag='NOT_ENOUGH_INFO',
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertFalse(MountMigrationRecord.objects.filter(from_gear=mount, image=image).exists())
        self.assertTrue(image.mounts.filter(pk=mount.pk).exists())

    def test_filter(self):
        image = Generators.image()
        filter = Generators.filter()

        image.filters.add(filter)

        migration_strategy = Generators.gear_migration_strategy(
            gear=filter,
            migration_flag='NOT_ENOUGH_INFO',
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertFalse(FilterMigrationRecord.objects.filter(from_gear=filter, image=image).exists())
        self.assertTrue(image.filters.filter(pk=filter.pk).exists())

    def test_accessory(self):
        image = Generators.image()
        accessory = Generators.accessory()

        image.accessories.add(accessory)

        migration_strategy = Generators.gear_migration_strategy(
            gear=accessory,
            migration_flag='NOT_ENOUGH_INFO',
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertFalse(AccessoryMigrationRecord.objects.filter(from_gear=accessory, image=image).exists())
        self.assertTrue(image.accessories.filter(pk=accessory.pk).exists())

    def test_focal_reducer(self):
        image = Generators.image()
        focal_reducer = Generators.focal_reducer()

        image.focal_reducers.add(focal_reducer)

        migration_strategy = Generators.gear_migration_strategy(
            gear=focal_reducer,
            migration_flag='NOT_ENOUGH_INFO',
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertFalse(FocalReducerMigrationRecord.objects.filter(from_gear=focal_reducer, image=image).exists())
        self.assertTrue(image.focal_reducers.filter(pk=focal_reducer.pk).exists())

    def test_software(self):
        image = Generators.image()
        software = Generators.software()

        image.software.add(software)

        migration_strategy = Generators.gear_migration_strategy(
            gear=software,
            migration_flag='NOT_ENOUGH_INFO',
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertFalse(SoftwareMigrationRecord.objects.filter(from_gear=software, image=image).exists())
        self.assertTrue(image.software.filter(pk=software.pk).exists())
