import math

from annoying.functions import get_object_or_None
from django.contrib.auth.models import User
from django.utils import timezone

from astrobin.models import CameraRenameProposal, Gear, GearMigrationStrategy, GearRenameRecord
from astrobin_apps_equipment.models import Camera, EquipmentBrand, Sensor
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_notifications.utils import push_notification


class GearService:
    """ Service related to the legacy models.Gear object """

    @staticmethod
    def reset_migration_fields(queryset):
        for item in queryset.iterator():
            GearMigrationStrategy.objects.filter(gear=item).delete()

        queryset.update(
            migration_flag_moderator_lock=None,
            migration_flag_moderator_lock_timestamp=None,
        )

    @staticmethod
    def process_camera_rename_proposal(proposal: CameraRenameProposal):
        if proposal.status != 'APPROVED':
            return

        if proposal.old_make == proposal.new_make and proposal.old_name == proposal.new_name:
            return

        astrobin_user = User.objects.get(username="astrobin")
        approvals = CameraRenameProposal.objects.filter(gear=proposal.gear, status='APPROVED').count()
        rejections = CameraRenameProposal.objects.filter(gear=proposal.gear, status='REJECTED').count()
        pending = CameraRenameProposal.objects.filter(gear=proposal.gear, status='PENDING').count()
        total = approvals + rejections + pending

        if rejections == 0 and (approvals == 5 or (approvals > 0 and approvals == math.ceil(total / 2))):
            Gear.objects \
                .filter(pk=proposal.gear.pk) \
                .update(make=proposal.new_make, name=proposal.new_name)

            CameraRenameProposal.objects \
                .filter(gear=proposal.gear, status='PENDING') \
                .update(status='AUTO_APPROVED')

            gear_rename_record = get_object_or_None(GearRenameRecord, gear=proposal.gear)
            if gear_rename_record:
                gear_rename_record.old_make=proposal.old_make
                gear_rename_record.old_name=proposal.old_name
                gear_rename_record.new_make=proposal.new_make
                gear_rename_record.new_name=proposal.new_name
                gear_rename_record.save()
            else:
                GearRenameRecord.objects.create(
                    gear=proposal.gear,
                    old_make=proposal.old_make,
                    old_name=proposal.old_name,
                    new_make=proposal.new_make,
                    new_name=proposal.new_name,
                )

            brand, created = EquipmentBrand.objects.get_or_create(
                name=proposal.new_make,
            )

            sensor = None
            if proposal.sensor_make and proposal.sensor_name:
                sensor_brand, created = EquipmentBrand.objects.get_or_create(
                    name=proposal.sensor_make,
                )

                sensor, created = Sensor.objects.get_or_create(
                    brand=sensor_brand,
                    name=proposal.sensor_name,
                )

            type = None
            if proposal.type == 'General purpose DSLR or mirrorless camera':
                type = CameraType.DSLR_MIRRORLESS
            elif proposal.type == 'Dedicated deep-sky camera':
                type = CameraType.DEDICATED_DEEP_SKY
            elif proposal.type == 'Guider/Planetary camera':
                type = CameraType.GUIDER_PLANETARY
            elif proposal.type == 'General purpose video camera':
                type = CameraType.VIDEO
            elif proposal.type == 'Film camera':
                type = CameraType.FILM
            else:
                type = CameraType.OTHER

            camera = get_object_or_None(
                Camera,
                brand=brand, name=proposal.new_name.replace(' (modified)', ''), modified=False)
            if camera:
                Camera.objects.filter(pk=camera.pk).update(
                    type=type,
                    sensor=sensor,
                    cooled=proposal.cooled,
                    created_by=astrobin_user,
                    reviewed_by=astrobin_user,
                    reviewed_timestamp=timezone.now(),
                    reviewer_decision='APPROVED',
                )
            else:
                camera, created = Camera.objects.get_or_create(
                    brand=brand,
                    name=proposal.new_name.replace(' (modified)', ''),
                    type=type,
                    sensor=sensor,
                    cooled=proposal.cooled,
                    modified=False,
                    created_by=astrobin_user,
                    reviewed_by=astrobin_user,
                    reviewed_timestamp=timezone.now(),
                    reviewer_decision='APPROVED',
                )

            if proposal.modified:
                camera = get_object_or_None(
                    Camera,
                    brand=brand, name=proposal.new_name.replace(' (modified)', ''), modified=True)
                if camera:
                    Camera.objects.filter(pk=camera.pk).update(
                        type=type,
                        sensor=sensor,
                        cooled=proposal.cooled,
                        created_by=astrobin_user,
                        reviewed_by=astrobin_user,
                        reviewed_timestamp=timezone.now(),
                        reviewer_decision='APPROVED',
                    )
                else:
                    camera, created = Camera.objects.get_or_create(
                        brand=brand,
                        name=proposal.new_name.replace(' (modified)', ''),
                        type=type,
                        sensor=sensor,
                        cooled=proposal.cooled,
                        modified=True,
                        created_by=astrobin_user,
                        reviewed_by=astrobin_user,
                        reviewed_timestamp=timezone.now(),
                        reviewer_decision='APPROVED',
                    )

            push_notification(
                list(set(list(User.objects.filter(userprofile__cameras__pk=proposal.gear.pk)))),
                None,
                'gear_renamed',
                {
                    'gear': proposal.gear,
                    'item': camera,
                }
            )
