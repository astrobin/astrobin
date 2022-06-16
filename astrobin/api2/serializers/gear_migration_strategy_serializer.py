from rest_framework import serializers

from astrobin.models import GearMigrationStrategy
from astrobin_apps_equipment.api.serializers.accessory_serializer import AccessorySerializer
from astrobin_apps_equipment.api.serializers.brand_serializer import BrandSerializer
from astrobin_apps_equipment.api.serializers.camera_serializer import CameraSerializer
from astrobin_apps_equipment.api.serializers.filter_serializer import FilterSerializer
from astrobin_apps_equipment.api.serializers.mount_serializer import MountSerializer
from astrobin_apps_equipment.api.serializers.software_serializer import SoftwareSerializer
from astrobin_apps_equipment.api.serializers.telescope_serializer import TelescopeSerializer
from astrobin_apps_equipment.models import Accessory, Camera, Filter, Mount, Software, Telescope


class MigrationContentObjectBrandField(serializers.RelatedField):
    def to_representation(self, value):
        if value.brand:
            return BrandSerializer().to_representation(value.brand)

        return None

    def to_internal_value(self, data):
        pass


class MigrationContentObjectField(serializers.RelatedField):
    def to_representation(self, value):
        if isinstance(value, Telescope):
            serializer = TelescopeSerializer()
        elif isinstance(value, Camera):
            serializer = CameraSerializer()
        elif isinstance(value, Mount):
            serializer = MountSerializer()
        elif isinstance(value, Filter):
            serializer = FilterSerializer()
        elif isinstance(value, Accessory):
            serializer = AccessorySerializer()
        elif isinstance(value, Software):
            serializer = SoftwareSerializer()
        else:
            raise Exception('Unexpected content object type')

        return serializer.to_representation(value)

    def to_internal_value(self, data):
        pass


class GearMigrationStrategySerializer(serializers.ModelSerializer):
    migration_content_object = MigrationContentObjectField(read_only=True)
    migration_content_object_brand = MigrationContentObjectBrandField(source='migration_content_object', read_only=True)

    class Meta:
        model = GearMigrationStrategy

        fields = (
            'pk',
            'gear',
            'user',
            'migration_flag',
            'migration_flag_timestamp',
            'migration_content_type',
            'migration_object_id',
            'migration_content_object',
            'migration_content_object_brand',
            'migration_flag_moderator',
            'migration_flag_reviewer_lock',
            'migration_flag_reviewer_lock_timestamp',
            'migration_flag_reviewer',
            'migration_flag_reviewer_decision',
        )

        depth = 1
