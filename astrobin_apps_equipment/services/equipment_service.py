class EquipmentService:
    @staticmethod
    def apply_migration_strategy(migration_strategy):
        from astrobin.models import Gear, GearMigrationStrategy, Image, Telescope, Camera, Mount, Filter, FocalReducer, Accessory, Software
        from astrobin_apps_equipment.models import (
            TelescopeMigrationRecord, CameraMigrationRecord,
            MountMigrationRecord, FilterMigrationRecord, FocalReducerMigrationRecord, AccessoryMigrationRecord,
            SoftwareMigrationRecord, MigrationUsageType
        )

        migration_strategy: GearMigrationStrategy = migration_strategy

        if migration_strategy.migration_flag != 'MIGRATE':
            return

        if migration_strategy.migration_flag_reviewer_decision != 'APPROVED':
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
