from annoying.functions import get_object_or_None

from astrobin_apps_equipment.models.deep_sky_acquisition_migration_record import DeepSkyAcquisitionMigrationRecord


class EquipmentService:
    @staticmethod
    def image_has_equipment_items(image) -> bool:
        return (
                image.imaging_telescopes_2.exists() or
                image.guiding_telescopes_2.exists() or
                image.mounts_2.exists() or
                image.imaging_cameras_2.exists() or
                image.guiding_cameras_2.exists() or
                image.software_2.exists() or
                image.filters_2.exists() or
                image.accessories_2.exists()
        )

    @staticmethod
    def apply_migration_strategy(migration_strategy):
        from astrobin.models import Gear, GearMigrationStrategy, Image, Telescope, Camera, Mount, Filter, FocalReducer, Accessory, Software
        from astrobin.models import DeepSky_Acquisition
        from astrobin_apps_equipment.models import (
            TelescopeMigrationRecord, CameraMigrationRecord,
            MountMigrationRecord, FilterMigrationRecord, FocalReducerMigrationRecord, AccessoryMigrationRecord,
            SoftwareMigrationRecord, MigrationUsageType
        )

        migration_strategy: GearMigrationStrategy = migration_strategy

        if migration_strategy.migration_flag != 'MIGRATE':
            return

        gear: Gear = migration_strategy.gear

        for usage_data in (
                ('imaging_telescopes', 'imaging_telescopes_2', Telescope, TelescopeMigrationRecord,
                 MigrationUsageType.IMAGING),
                ('guiding_telescopes', 'guiding_telescopes_2', Telescope, TelescopeMigrationRecord, MigrationUsageType.GUIDING),
                ('imaging_cameras', 'imaging_cameras_2', Camera, CameraMigrationRecord, MigrationUsageType.IMAGING),
                ('guiding_cameras', 'guiding_cameras_2', Camera, CameraMigrationRecord, MigrationUsageType.GUIDING),
                ('mounts', 'mounts_2', Mount, MountMigrationRecord, None),
                ('filters', 'filters_2', Filter, FilterMigrationRecord, None),
                ('focal_reducers', 'accessories_2', FocalReducer, FocalReducerMigrationRecord, None),
                ('accessories', 'accessories_2', Accessory, AccessoryMigrationRecord, None),
                ('software', 'software_2', Software, SoftwareMigrationRecord, None),
        ):
            usage = usage_data[0]
            new_usage = usage_data[1]
            GearKlass = usage_data[2]
            RecordKlass = usage_data[3]
            usage_type = usage_data[4]

            try:
                images = Image.objects_including_wip.filter(**{usage: gear})
            except ValueError:
                continue

            if not images.exists():
                continue

            classed_gear = GearKlass.objects.get(pk=gear.pk)

            if migration_strategy.user:
                images = images.filter(user=migration_strategy.user)

            for image in images.iterator():
                getattr(image, usage).remove(classed_gear)
                getattr(image, new_usage).add(migration_strategy.migration_content_object)

                params = dict(
                    image=image,
                    from_gear=classed_gear,
                    to_item=migration_strategy.migration_content_object
                )

                if usage_type:
                    params['usage_type'] = usage_type

                RecordKlass.objects.get_or_create(**params)

        try:
            deep_sky_acquisitions = DeepSky_Acquisition.objects.filter(
                image__user=migration_strategy.user,
                filter=Filter.objects.get(pk=gear.pk)
            )
            deep_sky_acquisition: DeepSky_Acquisition
            for deep_sky_acquisition in deep_sky_acquisitions.iterator():
                deep_sky_acquisition.filter = None
                deep_sky_acquisition.filter_2 = migration_strategy.migration_content_object
                deep_sky_acquisition.save()
                if not deep_sky_acquisition.image.filters_2.filter(pk=migration_strategy.migration_content_object.pk).exists():
                    deep_sky_acquisition.image.filters_2.add(migration_strategy.migration_content_object)
                DeepSkyAcquisitionMigrationRecord.objects.get_or_create(
                    deep_sky_acquisition=deep_sky_acquisition,
                    from_gear=Filter.objects.get(pk=gear.pk),
                    to_item=migration_strategy.migration_content_object
                )
        except Filter.DoesNotExist:
            pass

    @staticmethod
    def undo_migration_strategy(migration_strategy):
        from astrobin.models import (
            Gear, GearMigrationStrategy, DeepSky_Acquisition, Telescope as LegacyTelescope, Camera as LegacyCamera,
            Mount as LegacyMount, Filter as LegacyFilter, Accessory as LegacyAccessory, Software as LegacySoftware,
            FocalReducer
        )
        from astrobin_apps_equipment.models import (
            AccessoryMigrationRecord, CameraMigrationRecord, FilterMigrationRecord, MigrationUsageType,
            MountMigrationRecord, SoftwareMigrationRecord, TelescopeMigrationRecord, FocalReducerMigrationRecord,
        )

        migration_strategy: GearMigrationStrategy = migration_strategy
        if migration_strategy.migration_flag == 'MIGRATE':
            for RecordClass in (
                    (TelescopeMigrationRecord, 'telescopes', LegacyTelescope),
                    (CameraMigrationRecord, 'cameras', LegacyCamera),
                    (MountMigrationRecord, 'mounts', LegacyMount),
                    (FilterMigrationRecord, 'filters', LegacyFilter),
                    (AccessoryMigrationRecord, 'accessories', LegacyAccessory),
                    (SoftwareMigrationRecord, 'software', LegacySoftware),
            ):
                try:
                    records = RecordClass[0].objects.filter(
                        from_gear=migration_strategy.gear, image__user=migration_strategy.user
                    )
                except ValueError:
                    continue

                record: RecordClass[0]
                for record in records:
                    legacy_item = RecordClass[2].objects.get(pk=migration_strategy.gear.pk)
                    if hasattr(record, 'usage_type'):
                        if record.usage_type == MigrationUsageType.IMAGING:
                            getattr(record.image, f'imaging_{RecordClass[1]}_2').remove(
                                migration_strategy.migration_content_object
                            )
                            getattr(record.image, f'imaging_{RecordClass[1]}').add(
                                legacy_item
                            )
                        elif record.usage_type == MigrationUsageType.GUIDING:
                            getattr(record.image, f'guiding_{RecordClass[1]}_2').remove(
                                migration_strategy.migration_content_object
                            )
                            getattr(record.image, f'guiding_{RecordClass[1]}').add(
                                legacy_item
                            )
                    else:
                        getattr(record.image, f'{RecordClass[1]}_2').remove(
                            migration_strategy.migration_content_object
                        )
                        getattr(record.image, f'{RecordClass[1]}').add(
                            legacy_item
                        )

                records.delete()

            # Handle focal reducers separately because they are Accessories in the new equipment database.
            try:
                records = FocalReducerMigrationRecord.objects.filter(
                    from_gear=migration_strategy.gear, image__user=migration_strategy.user
                )

                for record in records:
                    legacy_item = FocalReducer.objects.get(pk=migration_strategy.gear.pk)
                    getattr(record.image, 'accessories_2').remove(migration_strategy.migration_content_object)
                    getattr(record.image, 'focal_reducers').add(legacy_item)

                records.delete()
            except ValueError:
                pass

            try:
                legacy_filter: LegacyFilter = LegacyFilter.objects.get(pk=migration_strategy.gear.pk)
                for deep_sky_acquisition_migration_record in DeepSkyAcquisitionMigrationRecord.objects.filter(
                        deep_sky_acquisition__image__user=migration_strategy.user,
                        from_gear=legacy_filter,
                        to_item=migration_strategy.migration_content_object
                ):
                    deep_sky_acquisition: DeepSky_Acquisition = deep_sky_acquisition_migration_record.deep_sky_acquisition
                    deep_sky_acquisition.filter = legacy_filter
                    deep_sky_acquisition.filter_2 = None
                    deep_sky_acquisition.save()
                    if not deep_sky_acquisition.image.filters_2.filter(pk=legacy_filter.pk).exists():
                        deep_sky_acquisition.image.filters.add(legacy_filter)
                    deep_sky_acquisition_migration_record.delete()
            except LegacyFilter.DoesNotExist:
                pass

        Gear.objects.filter(pk=migration_strategy.gear.pk).update(
            migration_flag_moderator_lock=None,
            migration_flag_moderator_lock_timestamp=None
        )

        migration_strategy.delete()
