import csv
from io import StringIO

from annoying.functions import get_object_or_None
from django.test import TestCase

from astrobin.models import DeepSky_Acquisition, Filter, GearMigrationStrategy, GearUserInfo, Image
from astrobin.tests.generators import Generators
from astrobin_apps_equipment.models import (
    AccessoryMigrationRecord, Camera, CameraMigrationRecord, EquipmentBrand, FilterMigrationRecord,
    FocalReducerMigrationRecord,
    MigrationUsageType, MountMigrationRecord,
    SoftwareMigrationRecord, TelescopeMigrationRecord,
)
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_equipment.models.deep_sky_acquisition_migration_record import DeepSkyAcquisitionMigrationRecord
from astrobin_apps_equipment.models import Filter as Filter2
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
            migration_flag_reviewer_decision='APPROVED'
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertTrue(
            TelescopeMigrationRecord.objects.filter(
                from_gear=telescope, to_item=new_telescope, image=image, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertFalse(image.imaging_telescopes.filter(pk=telescope.pk).exists())
        self.assertTrue(image.imaging_telescopes_2.filter(pk=new_telescope.pk).exists())

        # Test idempotency by applying the migration a second time

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertEquals(
            1,
            TelescopeMigrationRecord.objects.filter(
                from_gear=telescope, to_item=new_telescope, image=image, usage_type=MigrationUsageType.IMAGING
            ).count()
        )
        self.assertFalse(image.imaging_telescopes.filter(pk=telescope.pk).exists())
        self.assertTrue(image.imaging_telescopes_2.filter(pk=new_telescope.pk).exists())

        # Test undo

        EquipmentService.undo_migration_strategy(migration_strategy)

        self.assertFalse(
            TelescopeMigrationRecord.objects.filter(
                from_gear=telescope, to_item=new_telescope, image=image, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertTrue(image.imaging_telescopes.filter(pk=telescope.pk).exists())
        self.assertFalse(image.imaging_telescopes_2.filter(pk=new_telescope.pk).exists())

    def test_telescope_imaging_global_migration(self):
        moderator = Generators.user(groups=["equipment_moderators"])
        user_1 = Generators.user(groups=["own_equipment_migrators"])
        user_2 = Generators.user(groups=["own_equipment_migrators"])
        telescope = Generators.telescope()
        new_telescope = EquipmentGenerators.telescope()

        image_1 = Generators.image(user=user_1)
        image_2 = Generators.image(user=user_2)

        image_1.imaging_telescopes.add(telescope)
        image_2.imaging_telescopes.add(telescope)

        migration_strategy = Generators.gear_migration_strategy(
            gear=telescope,
            user=None,
            migration_flag='MIGRATE',
            migration_content_object=new_telescope,
            migration_flag_moderator=moderator,
            migration_flag_reviewer_decision='APPROVED'
        )

        self.assertTrue(GearMigrationStrategy.objects.filter(user=user_1, gear=telescope).exists())
        self.assertTrue(GearMigrationStrategy.objects.filter(user=user_2, gear=telescope).exists())

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertTrue(
            TelescopeMigrationRecord.objects.filter(
                from_gear=telescope, to_item=new_telescope, image=image_1, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertFalse(image_1.imaging_telescopes.filter(pk=telescope.pk).exists())
        self.assertTrue(image_1.imaging_telescopes_2.filter(pk=new_telescope.pk).exists())

        self.assertTrue(
            TelescopeMigrationRecord.objects.filter(
                from_gear=telescope, to_item=new_telescope, image=image_2, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertFalse(image_2.imaging_telescopes.filter(pk=telescope.pk).exists())
        self.assertTrue(image_2.imaging_telescopes_2.filter(pk=new_telescope.pk).exists())

        EquipmentService.undo_migration_strategy(migration_strategy)

        self.assertFalse(
            TelescopeMigrationRecord.objects.filter(
                from_gear=telescope, to_item=new_telescope, image=image_1, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertTrue(image_1.imaging_telescopes.filter(pk=telescope.pk).exists())
        self.assertFalse(image_1.imaging_telescopes_2.filter(pk=new_telescope.pk).exists())

        self.assertFalse(
            TelescopeMigrationRecord.objects.filter(
                from_gear=telescope, to_item=new_telescope, image=image_2, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertTrue(image_2.imaging_telescopes.filter(pk=telescope.pk).exists())
        self.assertFalse(image_2.imaging_telescopes_2.filter(pk=new_telescope.pk).exists())

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
            migration_flag_reviewer_decision='APPROVED'
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

    def test_camera_imaging_global_migration(self):
        moderator = Generators.user(groups=["equipment_moderators"])
        user_1 = Generators.user(groups=["own_equipment_migrators"])
        user_2 = Generators.user(groups=["own_equipment_migrators"])

        image_1 = Generators.image(user=user_1)
        image_2 = Generators.image(user=user_2)

        camera = Generators.camera()

        # user_2 has this cameras as modded. We want to test that when we create a global migration, user_2 gets
        # the modified version of the DSLR we will use.
        GearUserInfo.objects.create(gear=camera, user=user_2, modded=True)

        image_1.imaging_cameras.add(camera)
        image_2.imaging_cameras.add(camera)

        new_camera = EquipmentGenerators.camera(type=CameraType.DSLR_MIRRORLESS, modified=False, cooled=False)
        modified = Camera.objects.get(brand=new_camera.brand, name=new_camera.name, modified=True, cooled=False)

        migration_strategy = Generators.gear_migration_strategy(
            gear=camera,
            migration_flag='MIGRATE',
            migration_content_object=new_camera,
            migration_flag_reviewer_decision='APPROVED',
            migration_flag_moderator=moderator
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertTrue(
            CameraMigrationRecord.objects.filter(
                from_gear=camera, to_item=new_camera, image=image_1, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertFalse(image_1.imaging_cameras.filter(pk=camera.pk).exists())
        self.assertTrue(image_1.imaging_cameras_2.filter(pk=new_camera.pk).exists())

        self.assertTrue(
            CameraMigrationRecord.objects.filter(
                from_gear=camera, to_item=modified, image=image_2, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertFalse(image_2.imaging_cameras.filter(pk=camera.pk).exists())
        self.assertTrue(image_2.imaging_cameras_2.filter(pk=modified.pk).exists())

        EquipmentService.undo_migration_strategy(migration_strategy)

        self.assertFalse(
            CameraMigrationRecord.objects.filter(
                from_gear=camera, to_item=new_camera, image=image_1, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertTrue(image_1.imaging_cameras.filter(pk=camera.pk).exists())
        self.assertFalse(image_1.imaging_cameras_2.filter(pk=new_camera.pk).exists())

        self.assertFalse(
            CameraMigrationRecord.objects.filter(
                from_gear=camera, to_item=new_camera, image=image_2, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertTrue(image_2.imaging_cameras.filter(pk=camera.pk).exists())
        self.assertFalse(image_2.imaging_cameras_2.filter(pk=new_camera.pk).exists())

    def test_camera_imaging_global_migration_non_dslr(self):
        moderator = Generators.user(groups=["equipment_moderators"])
        user_1 = Generators.user(groups=["own_equipment_migrators"])
        user_2 = Generators.user(groups=["own_equipment_migrators"])

        image_1 = Generators.image(user=user_1)
        image_2 = Generators.image(user=user_2)

        camera = Generators.camera()

        # user_2 has this cameras as modded, but this test is not for a DSLR so they get the same camera as user_1
        GearUserInfo.objects.create(gear=camera, user=user_2, modded=True)

        image_1.imaging_cameras.add(camera)
        image_2.imaging_cameras.add(camera)

        new_camera = EquipmentGenerators.camera(type=CameraType.DEDICATED_DEEP_SKY, modified=False, cooled=False)

        migration_strategy = Generators.gear_migration_strategy(
            gear=camera,
            migration_flag='MIGRATE',
            migration_content_object=new_camera,
            migration_flag_reviewer_decision='APPROVED',
            migration_flag_moderator=moderator
        )

        EquipmentService.apply_migration_strategy(migration_strategy)

        self.assertTrue(
            CameraMigrationRecord.objects.filter(
                from_gear=camera, to_item=new_camera, image=image_1, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertFalse(image_1.imaging_cameras.filter(pk=camera.pk).exists())
        self.assertTrue(image_1.imaging_cameras_2.filter(pk=new_camera.pk).exists())

        self.assertTrue(
            CameraMigrationRecord.objects.filter(
                from_gear=camera, to_item=new_camera, image=image_2, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertFalse(image_2.imaging_cameras.filter(pk=camera.pk).exists())
        self.assertTrue(image_2.imaging_cameras_2.filter(pk=new_camera.pk).exists())

        EquipmentService.undo_migration_strategy(migration_strategy)

        self.assertFalse(
            CameraMigrationRecord.objects.filter(
                from_gear=camera, to_item=new_camera, image=image_1, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertTrue(image_1.imaging_cameras.filter(pk=camera.pk).exists())
        self.assertFalse(image_1.imaging_cameras_2.filter(pk=new_camera.pk).exists())

        self.assertFalse(
            CameraMigrationRecord.objects.filter(
                from_gear=camera, to_item=new_camera, image=image_2, usage_type=MigrationUsageType.IMAGING
            ).exists()
        )
        self.assertTrue(image_2.imaging_cameras.filter(pk=camera.pk).exists())
        self.assertFalse(image_2.imaging_cameras_2.filter(pk=new_camera.pk).exists())

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
            migration_flag_reviewer_decision='APPROVED'
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
            migration_flag_reviewer_decision='APPROVED'
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
            migration_flag_reviewer_decision='APPROVED'
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
            migration_flag_reviewer_decision='APPROVED'
        )

        # In this test scenario, filter_2 was migrated to new_filter by mistake. When undoing it, we will test that
        # only deep_sky_acquisition_2 gets the filters changed.
        migration_strategy_2 = Generators.gear_migration_strategy(
            gear=filter_2,
            user=user,
            migration_flag='MIGRATE',
            migration_content_object=new_filter,
            migration_fla_reviewer_decision='APPROVED'
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
        self.assertEquals(new_filter, deep_sky_acquisition_2.filter_2)
        self.assertIsNone(deep_sky_acquisition_2.filter)
        self.assertTrue(
            DeepSkyAcquisitionMigrationRecord.objects.filter(
                deep_sky_acquisition=deep_sky_acquisition_2,
                from_gear=filter_2,
                to_item=new_filter
            ).exists()
        )

        EquipmentService.apply_migration_strategy(migration_strategy_1)

        self.assertTrue(
            FilterMigrationRecord.objects.filter(
                from_gear=filter_1, to_item=new_filter, image=image
            ).exists()
        )
        self.assertFalse(image.filters.filter(pk=filter_1.pk).exists())
        self.assertTrue(image.filters_2.filter(pk=new_filter.pk).exists())
        deep_sky_acquisition_1.refresh_from_db()
        self.assertEquals(new_filter, deep_sky_acquisition_1.filter_2)
        self.assertIsNone(deep_sky_acquisition_1.filter)
        self.assertTrue(
            DeepSkyAcquisitionMigrationRecord.objects.filter(
                deep_sky_acquisition=deep_sky_acquisition_1,
                from_gear=filter_1,
                to_item=new_filter
            ).exists()
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
        self.assertEquals(filter_2, deep_sky_acquisition_2.filter)
        self.assertIsNone(deep_sky_acquisition_2.filter_2)

        self.assertTrue(
            FilterMigrationRecord.objects.filter(
                from_gear=filter_1, to_item=new_filter, image=image
            ).exists()
        )
        deep_sky_acquisition_1.refresh_from_db()
        self.assertEquals(new_filter, deep_sky_acquisition_1.filter_2)
        self.assertIsNone(deep_sky_acquisition_1.filter)
        self.assertTrue(
            DeepSkyAcquisitionMigrationRecord.objects.filter(from_gear=filter_1, to_item=new_filter).exists()
        )

    def test_filter_global_migration(self):
        moderator = Generators.user(groups=["equipment_moderators"])
        user_1 = Generators.user(groups=["own_equipment_migrators"])
        user_2 = Generators.user(groups=["own_equipment_migrators"])
        user_3 = Generators.user() # This user will not receive the migrations

        filter = Generators.filter()
        new_filter = EquipmentGenerators.filter()

        image_1 = Generators.image(user=user_1)
        image_2 = Generators.image(user=user_2)
        image_3 = Generators.image(user=user_3)

        image_1.filters.add(filter)
        image_2.filters.add(filter)
        image_3.filters.add(filter)

        deep_sky_acquisition_1 = DeepSky_Acquisition.objects.create(
            image=image_1,
            filter=filter,
            duration=300,
            number=10,
        )

        deep_sky_acquisition_2 = DeepSky_Acquisition.objects.create(
            image=image_2,
            filter=filter,
            duration=300,
            number=10,
        )

        deep_sky_acquisition_3 = DeepSky_Acquisition.objects.create(
            image=image_3,
            filter=filter,
            duration=300,
            number=10,
        )

        migration_strategy = Generators.gear_migration_strategy(
            gear=filter,
            user=None,
            migration_flag='MIGRATE',
            migration_content_object=new_filter,
            migration_flag_moderator=moderator,
            migration_flag_reviewer_decision='APPROVED'
        )

        self.assertTrue(GearMigrationStrategy.objects.filter(user=user_1, gear=filter).exists())
        self.assertTrue(GearMigrationStrategy.objects.filter(user=user_2, gear=filter).exists())
        # user_3 is not in own_equipment_migrators
        self.assertFalse(GearMigrationStrategy.objects.filter(user=user_3, gear=filter).exists())

        EquipmentService.apply_migration_strategy(migration_strategy)

        # Check user_1
        self.assertTrue(
            FilterMigrationRecord.objects.filter(
                from_gear=filter, to_item=new_filter, image=image_1
            ).exists()
        )
        self.assertFalse(image_1.filters.filter(pk=filter.pk).exists())
        self.assertTrue(image_1.filters_2.filter(pk=new_filter.pk).exists())
        deep_sky_acquisition_1.refresh_from_db()
        self.assertEquals(new_filter, deep_sky_acquisition_1.filter_2)
        self.assertIsNone(deep_sky_acquisition_1.filter)
        self.assertTrue(
            DeepSkyAcquisitionMigrationRecord.objects.filter(
                deep_sky_acquisition=deep_sky_acquisition_1,
                from_gear=filter,
                to_item=new_filter
            ).exists()
        )

        # Check user_2
        self.assertTrue(
            FilterMigrationRecord.objects.filter(
                from_gear=filter, to_item=new_filter, image=image_2
            ).exists()
        )
        self.assertFalse(image_2.filters.filter(pk=filter.pk).exists())
        self.assertTrue(image_2.filters_2.filter(pk=new_filter.pk).exists())
        deep_sky_acquisition_2.refresh_from_db()
        self.assertEquals(new_filter, deep_sky_acquisition_2.filter_2)
        self.assertIsNone(deep_sky_acquisition_2.filter)
        self.assertTrue(
            DeepSkyAcquisitionMigrationRecord.objects.filter(
                deep_sky_acquisition=deep_sky_acquisition_2,
                from_gear=filter,
                to_item=new_filter
            ).exists()
        )

        # Check user_3
        self.assertFalse(
            FilterMigrationRecord.objects.filter(
                from_gear=filter, to_item=new_filter, image=image_3
            ).exists()
        )
        self.assertTrue(image_3.filters.filter(pk=filter.pk).exists())
        self.assertFalse(image_3.filters_2.filter(pk=new_filter.pk).exists())
        deep_sky_acquisition_3.refresh_from_db()
        self.assertIsNone(deep_sky_acquisition_3.filter_2)
        self.assertEquals(filter, deep_sky_acquisition_3.filter)
        self.assertFalse(
            DeepSkyAcquisitionMigrationRecord.objects.filter(
                deep_sky_acquisition=deep_sky_acquisition_3,
                from_gear=filter,
                to_item=new_filter
            ).exists()
        )

        EquipmentService.undo_migration_strategy(migration_strategy)

        self.assertFalse(
            FilterMigrationRecord.objects.filter(
                from_gear=filter, to_item=new_filter, image=image_1
            ).exists()
        )
        self.assertTrue(image_1.filters.filter(pk=filter.pk).exists())
        self.assertFalse(image_1.filters_2.filter(pk=new_filter.pk).exists())
        deep_sky_acquisition_1.refresh_from_db()
        self.assertEquals(filter, deep_sky_acquisition_1.filter)
        self.assertIsNone(deep_sky_acquisition_1.filter_2)
        self.assertFalse(
            DeepSkyAcquisitionMigrationRecord.objects.filter(
                deep_sky_acquisition=deep_sky_acquisition_1,
                from_gear=filter,
                to_item=new_filter
            ).exists()
        )

        self.assertFalse(
            FilterMigrationRecord.objects.filter(
                from_gear=filter, to_item=new_filter, image=image_2
            ).exists()
        )
        self.assertTrue(image_2.filters.filter(pk=filter.pk).exists())
        self.assertFalse(image_2.filters_2.filter(pk=new_filter.pk).exists())
        deep_sky_acquisition_2.refresh_from_db()
        self.assertEquals(filter, deep_sky_acquisition_2.filter)
        self.assertIsNone(deep_sky_acquisition_2.filter_2)
        self.assertFalse(
            DeepSkyAcquisitionMigrationRecord.objects.filter(
                deep_sky_acquisition=deep_sky_acquisition_2,
                from_gear=filter,
                to_item=new_filter
            ).exists()
        )

    def test_filter_acquisitions(self):
        data = """702902, 620788, 113083
702918, 620788, 113083
702900, 620788, 140371
702904, 620788, 113083
702905, 620788, 113083
702898, 620788, 140371
702916, 620788, 113083
702915, 620788, 113083
702911, 620788, 113083
702903, 620788, 113083
723546, 634851, 140371
723545, 634851, 113083
723548, 634851, 140371
734301, 641531, 113083
734628, 641800, 113083
734629, 641800, 113083
734631, 641800, 113083
734632, 641800, 113083
734633, 641800, 113083
735402, 642383, 140371
735397, 642383, 140371
735396, 642383, 140371
735406, 642383, 140371
735408, 642383, 113083
735409, 642383, 113083
735410, 642383, 113083
735411, 642383, 113083
735412, 642383, 113083
735413, 642383, 113083
735416, 642383, 113083
735418, 642383, 113083
736102, 642430, 140371
736485, 643134, 140371
736486, 643134, 140371
736487, 643134, 140371
736489, 643134, 140371
736490, 643134, 140371
736817, 643329, 140371
736819, 643329, 140371
736929, 643405, 140371
736942, 643405, 140371
736946, 643405, 113083
736943, 643405, 140371
736941, 643405, 140371
736934, 643405, 140371
736933, 643405, 140371
736928, 643405, 140371
736948, 643405, 113083
737325, 643633, 140371
737326, 643633, 140371
737330, 643633, 140371
737331, 643633, 140371
737332, 643633, 140371
737333, 643633, 140371
737334, 643633, 140371
737338, 643633, 140371
737339, 643633, 113083
737399, 643699, 140371
737595, 643841, 113083
737596, 643841, 113083
737601, 643841, 113083
737602, 643841, 113083
737606, 643841, 140371
737613, 643841, 140371
737617, 643841, 140371
737624, 643841, 140371
737630, 643841, 140371
737660, 643896, 140371
737662, 643896, 140371
737663, 643896, 140371
737664, 643896, 140371
737666, 643896, 140371
737669, 643896, 140371
737672, 643896, 140371
737674, 643896, 140371
737926, 643915, 140371
737932, 643915, 140371
737949, 643915, 140371
737964, 643915, 113083
737971, 643915, 113083
737970, 643915, 113083
737962, 643915, 113083
737958, 643915, 140371
737956, 643915, 140371
737952, 643915, 140371
737951, 643915, 140371
737950, 643915, 140371
737933, 643915, 140371
737931, 643915, 140371
737966, 643915, 113083
738303, 644305, 140371
738304, 644305, 140371
738342, 644338, 140371
738345, 644338, 140371
738346, 644338, 140371
738347, 644338, 140371
738350, 644338, 140371
738354, 644338, 113083
738533, 644457, 140371
738535, 644457, 140371
738536, 644457, 140371
738539, 644457, 140371
738541, 644457, 140371
738542, 644457, 113083
738617, 644515, 140371
738618, 644515, 140371
738620, 644515, 140371
738622, 644515, 140371
738624, 644515, 140371
738625, 644515, 140371
738627, 644515, 140371
738628, 644515, 140371
738629, 644515, 140371
739454, 645093, 140371
739457, 645093, 140371
739461, 645093, 140371
739464, 645093, 113083
739465, 645093, 113083
739466, 645093, 113083
739467, 645093, 113083
739932, 645428, 140371
740259, 645598, 140371
740260, 645598, 140371
740261, 645598, 140371
740262, 645598, 140371
740263, 645598, 140371
740264, 645598, 113083
736935, 643405, 140371
736952, 643405, 113083
740410, 645723, 140371
740413, 645723, 140371
740414, 645723, 140371
740416, 645723, 140371
740417, 645723, 140371
740421, 645723, 113083
740424, 645723, 139777
740426, 645723, 113083
740428, 645723, 113083
740868, 645992, 140371
740869, 645992, 140371
736484, 643134, 140371
741058, 646112, 140371
741059, 646112, 140371
741061, 646112, 140371
741064, 646112, 140371
741065, 646112, 140371
741067, 646112, 113083
741072, 646112, 113083
741068, 646112, 113083
741221, 646204, 140371
741222, 646204, 140371
741223, 646204, 140371
741280, 646259, 140371
741281, 646259, 140371
741285, 646259, 140371
741286, 646259, 140371
741349, 646304, 140371
741348, 646304, 140371
741355, 646304, 140371
741430, 646345, 140371
741431, 646345, 140371
741432, 646345, 140371
741433, 646345, 140371
741434, 646345, 140371
741435, 646345, 113083
746980, 649593, 140371
746981, 649593, 140371
747033, 649619, 140371
747035, 649619, 140371
747038, 649619, 140371
750323, 651972, 140371
750325, 651972, 140371
750327, 651972, 140371
750328, 651972, 113083
750329, 651972, 113083
759782, 658579, 140371
759783, 658579, 140371
759784, 658579, 140371
759792, 658579, 140371
759847, 658579, 140371
759879, 658579, 140371
759880, 658579, 140371
759883, 658579, 140371
759884, 658579, 140371
759785, 658579, 140371
759786, 658579, 140371
759787, 658579, 140371
759788, 658579, 140371
759789, 658579, 140371
759793, 658579, 140371
759794, 658579, 140371
759795, 658579, 140371
759797, 658579, 140371
759837, 658579, 140371
759838, 658579, 140371
759839, 658579, 140371
759840, 658579, 140371
759841, 658579, 140371
759842, 658579, 140371
759844, 658579, 140371
759845, 658579, 140371
759846, 658579, 140371
759848, 658579, 140371
759851, 658579, 140371
759852, 658579, 140371
759853, 658579, 113083
759854, 658579, 113083
759855, 658579, 113083
759859, 658579, 113083
759862, 658579, 113083
759864, 658579, 113083
759866, 658579, 113083
759867, 658579, 113083
759868, 658579, 113083
759870, 658579, 113083
759871, 658579, 113083
759872, 658579, 113083
766532, 663093, 140371
766534, 663093, 148591
766535, 663093, 148591
766536, 663093, 148591
766538, 663093, 148591
766539, 663093, 148591
766540, 663093, 148591
766541, 663093, 148591
766548, 663093, 148591
766549, 663093, 148591
766550, 663093, 148591
766551, 663093, 148591
766552, 663093, 148591
766553, 663093, 148591
759873, 658579, 148591
759874, 658579, 148591
759876, 658579, 148591
750330, 651972, 148591
750331, 651972, 148591
747040, 649619, 148591
747041, 649619, 148591
747042, 649619, 148591
747043, 649619, 148591
747044, 649619, 148591
747045, 649619, 148591
747051, 649619, 148591
741074, 646112, 148591
741075, 646112, 148591
741076, 646112, 148591
741079, 646112, 148591
741082, 646112, 148591
741091, 646112, 148591
741147, 646174, 148591
741152, 646174, 148591
741153, 646174, 148591
735420, 642383, 148591
735423, 642383, 148591
735424, 642383, 148591
735425, 642383, 148591
735426, 642383, 148591
735427, 642383, 148591
735428, 642383, 148591
735435, 642383, 148591
723526, 634851, 148591
723528, 634851, 148591
723532, 634851, 148591
723536, 634851, 148591
723539, 634851, 148591
723544, 634851, 148591
702919, 620788, 148591
702920, 620788, 148591
702921, 620788, 148591
702922, 620788, 148591
737961, 643915, 148591
770457, 665717, 140371
770459, 665717, 140371
770460, 665717, 140371
770461, 665717, 140371
770462, 665717, 140371
770463, 665717, 140371
770465, 665717, 140371
770466, 665717, 140371
770468, 665717, 140371
770469, 665717, 140371
770471, 665717, 140371
770474, 665717, 140371
770477, 665717, 140371
770478, 665717, 140371
770479, 665717, 140371
770480, 665717, 140371
770481, 665717, 140371
770482, 665717, 140371
770483, 665717, 140371
770484, 665717, 140371
770485, 665717, 140371
770486, 665717, 140371
770487, 665717, 140371
770488, 665717, 140371
770489, 665717, 140371
770490, 665717, 140371
770492, 665717, 140371
770494, 665717, 140371
770495, 665717, 140371
770498, 665717, 140371
770500, 665717, 113083
770501, 665717, 113083
770502, 665717, 113083
770503, 665717, 113083
770505, 665717, 113083
770506, 665717, 113083
770507, 665717, 113083
770508, 665717, 113083
770509, 665717, 113083
770510, 665717, 113083
770511, 665717, 113083
770512, 665717, 113083
770513, 665717, 113083
770514, 665717, 113083
770515, 665717, 113083
770517, 665717, 113083
770518, 665717, 113083
770519, 665717, 113083
770520, 665717, 113083
770522, 665717, 148591
790828, 678830, 140371
790829, 678830, 140371
790830, 678830, 140371
790831, 678830, 140371
790832, 678830, 148591
790833, 678830, 148591
790834, 678830, 148591
790835, 678830, 148591
790836, 678830, 148591
790837, 678830, 148591
790839, 678830, 148591
790842, 678830, 148591
790843, 678830, 148591
790848, 678830, 148591
790851, 678830, 148591
790853, 678830, 148591
790855, 678830, 148591
790859, 678830, 102116
790860, 678830, 102116
790861, 678830, 102116
790838, 678830, 148591
798857, 684714, 140371
798859, 684714, 148591
798861, 684714, 148591
798966, 684785, 140371
798967, 684785, 148591
802325, 687223, 140371
802323, 687223, 140371
802324, 687223, 140371
802326, 687223, 140371
802328, 687223, 140371
802329, 687223, 140371
802335, 687223, 113083
802338, 687223, 113083
802341, 687223, 113083
802342, 687223, 113083
802344, 687223, 148591
802345, 687223, 148591
802346, 687223, 148591
802331, 687223, 140371
802327, 687223, 140371
798968, 684785, 148591
806761, 690558, 140371
806765, 690558, 140371
806766, 690558, 140371
806768, 690558, 140371
806769, 690558, 140371
806776, 690558, 148591
806777, 690558, 148591
806778, 690558, 148591
806779, 690558, 148591
806781, 690558, 148591
806782, 690558, 148591
806783, 690558, 148591
806793, 690558, 148591
807462, 691151, 140371
807461, 691151, 140371
807463, 691151, 140371
807464, 691151, 140371
807465, 691151, 140371
807466, 691151, 140371
809399, 692577, 140371
810252, 693213, 113083
810253, 693213, 140371
810254, 693213, 140371
813615, 695469, 140371
813617, 695469, 140371
813622, 695469, 140371
815591, 696777, 140371
815592, 696777, 140371
815593, 696777, 140371
815595, 696777, 140371
815596, 696777, 140371
815605, 696777, 113083
815606, 696777, 113083
815607, 696777, 113083
815610, 696777, 113083
817203, 697758, 140371
817205, 697758, 140371
817206, 697758, 140371
817207, 697758, 140371"""
        data_array = []
        f = StringIO(data)
        reader = csv.reader(f, delimiter=',')

        user = Generators.user()

        for row in reader:
            data_array.append(row)

        for row in data_array:
            acquisition_id = row[0]
            image_id = row[1]
            filter_id = row[2]

            image = get_object_or_None(Image, id=image_id)
            if not image:
                image = Generators.image(user=user)
                Image.objects.filter(pk=image.pk).update(id=image_id)
                image = Image.objects.get(id=image_id)

            legacy_filter = get_object_or_None(Filter, id=filter_id)
            if not legacy_filter:
                legacy_filter = Generators.filter(name=filter_id)
                Filter.objects.filter(pk=legacy_filter.pk).update(id=filter_id, gear_ptr_id=filter_id)
                legacy_filter = Filter.objects.get(id=filter_id)

            DeepSky_Acquisition.objects.create(
                id=acquisition_id,
                image=image,
                filter=legacy_filter
            )

            filter_2 = get_object_or_None(Filter2, brand__name=legacy_filter.make, name=legacy_filter.name)
            if not filter_2:
                brand, created = EquipmentBrand.objects.get_or_create(name=legacy_filter.make)
                EquipmentGenerators.filter(brand=brand, name=legacy_filter.name)

        for legacy_filter in Filter.objects.all().iterator():
            Generators.gear_migration_strategy(
                gear=legacy_filter,
                user=user,
                migration_flag='MIGRATE',
                migration_content_object=Filter2.objects.get(brand__name=legacy_filter.make, name=legacy_filter.name),
                migration_flag_reviewer_decision='APPROVED'
            )

        for acquisition in DeepSky_Acquisition.objects.all().iterator():
            self.assertIsNone(acquisition.filter)
            self.assertIsNotNone(acquisition.filter_2)

        for migration_strategy in GearMigrationStrategy.objects.all().iterator():
            EquipmentService.undo_migration_strategy(migration_strategy)

        for acquisition in DeepSky_Acquisition.objects.all().iterator():
            self.assertIsNone(acquisition.filter_2)
            self.assertIsNotNone(acquisition.filter)

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
            migration_flag_reviewer_decision='APPROVED'
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
            migration_fla_reviewer_decision='APPROVED'
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
            migration_flag_reviewer_decision='APPROVED'
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
