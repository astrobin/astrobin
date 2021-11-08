from django.contrib.auth.models import User

from astrobin.models import CameraRenameProposal, Gear, GearRenameRecord, UserProfile
from astrobin_apps_equipment.models import Camera, EquipmentBrand, Sensor
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_notifications.utils import push_notification


class GearService:
    """ Service related to the legacy models.Gear object """

    @staticmethod
    def reset_migration_fields(queryset):
        queryset.update(
            migration_flag=None,
            migration_flag_timestamp=None,
            migration_content_type=None,
            migration_object_id=None,
            migration_flag_moderator=None,
            migration_flag_moderator_lock=None,
            migration_flag_moderator_lock_timestamp=None,
            migration_flag_reviewer=None,
            migration_flag_reviewer_lock=None,
            migration_flag_reviewer_lock_timestamp=None,
            migration_flag_reviewer_decision=None,
            migration_flag_reviewer_rejection_comment=None
        )

    @staticmethod
    def process_camera_rename_proposal(proposal: CameraRenameProposal):
        approvals = CameraRenameProposal.objects.filter(gear=proposal.gear, status='APPROVED').count()
        rejections = CameraRenameProposal.objects.filter(gear=proposal.gear, status='REJECTED').count()
        pending = CameraRenameProposal.objects.filter(gear=proposal.gear, status='PENDING').count()
        total = approvals + rejections + pending

        if rejections == 0 and (approvals >= 5 or approvals >= total / 2):
            Gear.objects \
                .filter(pk=proposal.gear.pk) \
                .update(make=proposal.new_make, name=proposal.new_name)

            CameraRenameProposal.objects \
                .filter(gear=proposal.gear, status='PENDING') \
                .update(status='AUTO_APPROVED')

            GearRenameRecord.objects.get_or_create(
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
            else:
                type = CameraType.OTHER

            camera, created = Camera.objects.get_or_create(
                brand=brand,
                name=proposal.new_name.replace(' (modified)', ''),
                type=type,
                sensor=sensor,
                cooled=proposal.cooled,
                modified=False,
            )

            if proposal.modified:
                Camera.objects.get_or_create(
                    brand=brand,
                    name=proposal.new_name.replace(' (modified)', ''),
                    type=type,
                    sensor=sensor,
                    cooled=proposal.cooled,
                    modified=True,
                )

            push_notification(
                list(User.objects.filter(userprofile__cameras__pk=proposal.gear.pk)),
                None,
                'gear_renamed',
                {
                    'gear': proposal.gear,
                    'item': camera,
                }
            )
