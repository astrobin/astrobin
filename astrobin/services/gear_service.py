import math

from annoying.functions import get_object_or_None
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext

from astrobin.models import CameraRenameProposal, Gear, GearMigrationStrategy, GearRenameRecord, GearUserInfo, Image
from astrobin_apps_equipment.models import Camera, EquipmentBrand, Sensor
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_equipment.services import EquipmentService
from astrobin_apps_notifications.utils import build_notification_url, push_notification
from common.services import AppRedirectionService


class GearService:
    """ Service related to the legacy models.Gear object """
    gear = None

    def __init__(self, gear=None):
        self.gear = gear

    @staticmethod
    def reset_migration_fields(queryset):
        for item in queryset.iterator():
            GearMigrationStrategy.objects.filter(gear=item).delete()

        queryset.update(
            migration_flag_moderator_lock=None,
            migration_flag_moderator_lock_timestamp=None,
        )

    @staticmethod
    def approve_migration_strategy(
            strategy: GearMigrationStrategy, reviewer: User, reason: str = None, comment: str = None
    ) -> GearMigrationStrategy:
        strategy.migration_flag_reviewer = reviewer
        strategy.migration_flag_reviewer_decision = 'APPROVED'
        strategy.migration_flag_reviewer_lock = None
        strategy.migration_flag_reviewer_lock_timestamp = None
        strategy.save()

        strategy.gear.migration_flag_moderator_lock = None
        strategy.gear.migration_flag_moderator_lock_timestamp = None
        strategy.gear.save()

        EquipmentService.apply_migration_strategy(strategy)

        target = strategy.migration_content_object

        if strategy.migration_flag_moderator and strategy.migration_flag_moderator != reviewer:
            push_notification(
                [strategy.migration_flag_moderator],
                reviewer,
                'equipment-item-migration-approved',
                {
                    'user': reviewer.userprofile.get_display_name(),
                    'user_url': build_notification_url(
                        settings.BASE_URL + reverse('user_page', args=(reviewer.username,))
                    ),
                    'migration_flag': strategy.migration_flag,
                    'reason': reason,
                    'comment': comment,
                    'legacy_item': strategy.gear,
                    'target_item': f'{target.brand.name if target.brand else gettext("(DIY)")} {target.name}' if target else None,
                    'target_url': build_notification_url(
                        AppRedirectionService.redirect(
                            f'/equipment'
                            f'/explorer'
                            f'/{target.item_type}/{target.pk}'
                            f'/{target.slug}'
                        )
                    ) if target else None,
                }
            )

        return strategy

    @staticmethod
    def reject_migration_strategy(
            strategy: GearMigrationStrategy, reviewer: User, reason: str, comment: str
    ) -> GearMigrationStrategy:
        target = strategy.migration_content_object

        if strategy.migration_flag_moderator and strategy.migration_flag_moderator != reviewer:
            push_notification(
                [strategy.migration_flag_moderator],
                reviewer,
                'equipment-item-migration-rejected',
                {
                    'user': reviewer.userprofile.get_display_name(),
                    'user_url': build_notification_url(
                        settings.BASE_URL + reverse('user_page', args=(reviewer.username,))
                    ),
                    'migration_flag': strategy.migration_flag,
                    'reason': reason,
                    'comment': comment,
                    'legacy_item': strategy.gear,
                    'target_item': f'{target.brand.name if target.brand else gettext("(DIY)")} {target.name}' if target else None,
                    'target_url': build_notification_url(
                        AppRedirectionService.redirect(
                            f'/equipment'
                            f'/explorer'
                            f'/{target.item_type}/{target.pk}'
                            f'/{target.slug}'
                        )
                    ) if target else None,
                    'migration_tool_url': build_notification_url(
                        AppRedirectionService.redirect(
                            f'/equipment'
                            f'/migration-tool'
                        )
                    ) if target else None,
                }
            )

        strategy.gear.migration_flag_moderator_lock = None
        strategy.gear.migration_flag_moderator_lock_timestamp = None
        strategy.gear.save()

        strategy.delete()

        return strategy

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

            for user in list(set(list(User.objects.filter(userprofile__cameras__pk=proposal.gear.pk)))):
                push_notification(
                    [user],
                    None,
                    'gear_renamed',
                    {
                        'gear_display_name': GearService(proposal.gear).display_name(for_user=user),
                        'item': camera,
                    }
                )

    @staticmethod
    def image_has_legacy_gear(image: Image) -> bool:
        return (
            image.imaging_telescopes.exists() or
            image.guiding_telescopes.exists() or
            image.mounts.exists() or
            image.imaging_cameras.exists() or
            image.guiding_cameras.exists() or
            image.focal_reducers.exists() or
            image.software.exists() or
            image.filters.exists() or
            image.accessories.exists()
        )

    @staticmethod
    def has_unmigrated_legacy_gear_items(user: User) -> bool:
        for image in Image.objects_including_wip.filter(user=user):
            for usage_class in (
                    'imaging_telescopes',
                    'imaging_cameras',
                    'mounts',
                    'filters',
                    'focal_reducers',
                    'accessories',
                    'software',
                    'guiding_telescopes',
                    'guiding_cameras'):
                if getattr(image, usage_class) \
                        .annotate(count=Count('migration_strategies', filter=Q(migration_strategies__user=user))) \
                        .filter(count=0) \
                        .exists():
                    return True

        return False

    def display_name(self, for_user: User = None):
        if for_user is None:
            return str(self.gear)

        gear_user_info: GearUserInfo = get_object_or_None(GearUserInfo, gear=self.gear, user=for_user)
        if gear_user_info is None:
            return str(self.gear)

        return str(gear_user_info)
