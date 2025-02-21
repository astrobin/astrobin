from datetime import datetime, timedelta
from typing import Optional

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from subscription.models import UserSubscription

from astrobin.api2.serializers.accessory_serializer import AccessorySerializer
from astrobin.api2.serializers.camera_serializer import CameraSerializer
from astrobin.api2.serializers.filter_serializer import FilterSerializer
from astrobin.api2.serializers.focal_reducer_serializer import FocalReducerSerializer
from astrobin.api2.serializers.location_serializer import LocationSerializer
from astrobin.api2.serializers.mount_serializer import MountSerializer
from astrobin.api2.serializers.software_serializer import SoftwareSerializer
from astrobin.api2.serializers.telescope_serializer import TelescopeSerializer
from astrobin.enums.mouse_hover_image import MouseHoverImage
from astrobin.models import DeepSky_Acquisition, Image, SolarSystem_Acquisition
from astrobin.moon import MoonPhase
from astrobin.services.utils_service import UtilsService
from astrobin_apps_equipment.api.serializers.accessory_serializer import (
    AccessorySerializerForImage,
)
from astrobin_apps_equipment.api.serializers.camera_serializer import (
    CameraSerializerForImage,
)
from astrobin_apps_equipment.api.serializers.filter_serializer import (
    FilterSerializerForImage,
)
from astrobin_apps_equipment.api.serializers.mount_serializer import (
    MountSerializerForImage,
)
from astrobin_apps_equipment.api.serializers.software_serializer import (
    SoftwareSerializerForImage,
)
from astrobin_apps_equipment.api.serializers.telescope_serializer import (
    TelescopeSerializerForImage,
)
from astrobin_apps_images.api.fields import KeyValueTagsSerializerField
from astrobin_apps_images.api.serializers import ImageRevisionSerializer
from astrobin_apps_images.api.serializers.deep_sky_acquisition_serializer import DeepSkyAcquisitionSerializer
from astrobin_apps_images.api.serializers.solar_system_acquisition_serializer import SolarSystemAcquisitionSerializer
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_platesolving.serializers import SolutionSerializer
from astrobin_apps_premium.services.premium_service import PremiumService
from common.serializers import AvatarField, UserSerializer
from common.templatetags.common_tags import strip_html


class ImageSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    username = serializers.CharField(source='user.username', read_only=True)
    user_display_name = serializers.CharField(source='user.userprofile.get_display_name', read_only=True)
    user_avatar = AvatarField(source='user', read_only=True)
    allow_ads = serializers.SerializerMethodField(read_only=True)
    hash = serializers.PrimaryKeyRelatedField(read_only=True)
    w = serializers.IntegerField()
    h = serializers.IntegerField()
    uploader_in_progress = serializers.NullBooleanField(read_only=True)
    key_value_tags = KeyValueTagsSerializerField(source='keyvaluetags')

    imaging_telescopes = TelescopeSerializer(many=True, read_only=True)
    imaging_cameras = CameraSerializer(many=True, read_only=True)
    guiding_telescopes = TelescopeSerializer(many=True, read_only=True)
    guiding_cameras = CameraSerializer(many=True, read_only=True)
    focal_reducers = FocalReducerSerializer(many=True, read_only=True)
    mounts = MountSerializer(many=True, read_only=True)
    filters = FilterSerializer(many=True, read_only=True)
    accessories = AccessorySerializer(many=True, read_only=True)
    software = SoftwareSerializer(many=True, read_only=True)

    imaging_telescopes_2 = TelescopeSerializerForImage(many=True, required=False)
    imaging_cameras_2 = CameraSerializerForImage(many=True, required=False)
    guiding_telescopes_2 = TelescopeSerializerForImage(many=True, required=False)
    guiding_cameras_2 = CameraSerializerForImage(many=True, required=False)
    mounts_2 = MountSerializerForImage(many=True, required=False)
    filters_2 = FilterSerializerForImage(many=True, required=False)
    accessories_2 = AccessorySerializerForImage(many=True, required=False)
    software_2 = SoftwareSerializerForImage(many=True, required=False)

    deep_sky_acquisitions = DeepSkyAcquisitionSerializer(many=True, required=False, read_only=True)
    solar_system_acquisitions = SolarSystemAcquisitionSerializer(many=True, required=False, read_only=True)

    video_file = serializers.FileField(required=False, allow_null=True, read_only=True)
    encoded_video_file = serializers.FileField(required=False, allow_null=True, read_only=True)

    solution = SolutionSerializer(read_only=True)
    revisions = serializers.SerializerMethodField()
    user_follower_count = serializers.SerializerMethodField(read_only=True)
    location_objects = LocationSerializer(source="locations", many=True, read_only=True)
    collaborators = UserSerializer(many=True, read_only=True)
    iotd_date = serializers.DateField(source="iotd.date", read_only=True)
    is_in_iotd_queue = serializers.SerializerMethodField(read_only=True)
    is_iotd = serializers.SerializerMethodField(read_only=True)
    is_top_pick = serializers.SerializerMethodField(read_only=True)
    is_top_pick_nomination = serializers.SerializerMethodField(read_only=True)
    average_moon_age = serializers.SerializerMethodField(read_only=True)
    average_moon_illumination = serializers.SerializerMethodField(read_only=True)

    default_max_zoom = serializers.IntegerField(source='user.userprofile.default_max_zoom', read_only=True)
    default_allow_image_adjustments_widget = serializers.BooleanField(
        source='user.userprofile.default_allow_image_adjustments_widget', read_only=True
    )

    detected_language = serializers.SerializerMethodField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iotd_service = IotdService()

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def to_representation(self, instance: Image):
        # Pass the current Image instance to the context of the nested serializer
        self.fields['revisions'].context.update({'image': instance})

        representation = super().to_representation(instance)
        thumbnails = [
            {
                'alias': alias,
                'id': instance.pk,
                'revision': 'final',
                'url': instance.thumbnail(alias, None, sync=True)
            } for alias in ('gallery', 'story', 'regular', 'hd', 'qhd')
        ]

        if not instance.is_final:
            thumbnails += [
                {
                    'alias': alias,
                    'id': instance.pk,
                    'revision': '0',
                    'url': instance.thumbnail(alias, '0', sync=True)
                } for alias in ('gallery', 'story', 'regular', 'hd', 'qhd')
            ]

        if instance.mouse_hover_image == MouseHoverImage.INVERTED:
            thumbnails += [
                {
                    'alias': 'hd_inverted',
                    'id': instance.pk,
                    'revision': '0',
                    'url': instance.thumbnail('hd_inverted', '0', sync=True)
                },
                {
                    'alias': 'qhd_inverted',
                    'id': instance.pk,
                    'revision': '0',
                    'url': instance.thumbnail('qhd_inverted', '0', sync=True)
                }
            ]

        if (
                instance.is_final and
                instance.submitted_for_iotd_tp_consideration and
                instance.submitted_for_iotd_tp_consideration > datetime.now() - timedelta(days=60)
        ):
            # Add hd_anonymized only if it's available (for IOTD/TP queue purposes)
            thumbnail_group = instance.thumbnails.filter(
                revision='0',
                hd_anonymized__isnull=False,
                hd_anonymized_crop__isnull=False,
            ).first()
            if thumbnail_group:
                thumbnails.append(
                    {
                        'alias': 'hd_anonymized',
                        'id': instance.pk,
                        'revision': 'final',
                        'url': thumbnail_group.hd_anonymized
                    }
                )
                thumbnails.append(
                    {
                        'alias': 'hd_anonymized_crop',
                        'id': instance.pk,
                        'revision': 'final',
                        'url': thumbnail_group.hd_anonymized_crop
                    }
                )

        representation.update({'thumbnails': thumbnails})
        representation.update(self.acquisitions_representation(instance))

        if instance.image_file and instance.image_file.name.lower().endswith('.gif'):
            representation.update({'image_file': instance.image_file.url})

        if self.context['request'].user == instance.user:
            representation['image_file'] = instance.image_file.url if instance.image_file else None
            representation['video_file'] = instance.video_file.url if instance.video_file else None
            representation['uncompressed_source_file'] = instance.uncompressed_source_file.url \
                if instance.uncompressed_source_file \
                else None

        return representation

    @staticmethod
    def acquisitions_representation(instance: Image):
        return {
            'deep_sky_acquisitions': DeepSkyAcquisitionSerializer(
                DeepSky_Acquisition.objects.filter(image=instance), many=True
            ).data,
            'solar_system_acquisitions': SolarSystemAcquisitionSerializer(
                SolarSystem_Acquisition.objects.filter(image=instance), many=True
            ).data
        }

    def validate_pending_collaborators(self, pending_collaborators):
        if pending_collaborators and self.initial_data.get('user') in [x.id for x in pending_collaborators]:
            raise ValidationError("Please do not include the image's user as a collaborator")

        return pending_collaborators

    def get_allow_ads(self, obj: Image) -> bool:
        valid_usersubscription: UserSubscription = PremiumService(obj.user).get_valid_usersubscription()
        is_ultimate: bool = valid_usersubscription and PremiumService.is_any_ultimate(valid_usersubscription)
        allow_ads = obj.user.userprofile.allow_astronomy_ads
        return allow_ads or not is_ultimate

    def get_revisions(self, obj):
        revisions = obj.revisions.filter(deleted__isnull=True)
        return ImageRevisionSerializer(revisions, many=True, context=self.context).data

    def get_user_follower_count(self, obj) -> int:
        return obj.user.userprofile.followers_count

    def get_is_in_iotd_queue(self, obj) -> bool:
        return self.iotd_service.is_in_iotd_queue(obj)

    def get_is_iotd(self, obj) -> bool:
        return self.iotd_service.is_iotd(obj)

    def get_is_top_pick(self, obj) -> bool:
        return self.iotd_service.is_top_pick(obj)

    def get_is_top_pick_nomination(self, obj) -> bool:
        return self.iotd_service.is_top_pick_nomination(obj)

    def get_average_moon_age(self, obj) -> Optional[float]:
        data = []
        for acquisition in DeepSky_Acquisition.objects.filter(image=obj, date__isnull=False).iterator():
            data.append(MoonPhase(acquisition.date).age)

        return sum(data) / len(data) if data else None

    def get_average_moon_illumination(self, obj: Image) -> Optional[float]:
        data = []

        for acquisition in DeepSky_Acquisition.objects.filter(image=obj, date__isnull=False).iterator():
            data.append(MoonPhase(acquisition.date).illuminated)

        if len(data) == 0:
            for acquisition in SolarSystem_Acquisition.objects.filter(image=obj, date__isnull=False).iterator():
                data.append(MoonPhase(acquisition.date).illuminated)

        return sum(data) / len(data) if data else None

    def get_detected_language(self, obj: Image) -> str:
        if obj.description_bbcode:
            return UtilsService.detect_language(UtilsService.strip_bbcode(obj.description_bbcode))

        if obj.description:
            return UtilsService.detect_language(strip_html(obj.description))

        return 'unknown'

    class Meta:
        model = Image
        fields = (
            'pk',
            'user',
            'username',
            'user_display_name',
            'user_avatar',
            'allow_ads',
            'pending_collaborators',
            'collaborators',
            'hash',
            'title',
            'is_wip',
            'skip_notifications',
            'skip_activity_stream',
            'w',
            'h',
            'imaging_telescopes',
            'imaging_cameras',
            'guiding_telescopes',
            'guiding_cameras',
            'focal_reducers',
            'mounts',
            'filters',
            'accessories',
            'software',
            'imaging_telescopes_2',
            'imaging_cameras_2',
            'guiding_telescopes_2',
            'guiding_cameras_2',
            'mounts_2',
            'filters_2',
            'accessories_2',
            'software_2',
            'published',
            'uploaded',
            'license',
            'description',
            'description_bbcode',
            'link',
            'link_to_fits',
            'acquisition_type',
            'deep_sky_acquisitions',
            'solar_system_acquisitions',
            'subject_type',
            'solar_system_main_subject',
            'data_source',
            'remote_source',
            'part_of_group_set',
            'collections',
            'mouse_hover_image',
            'allow_comments',
            'uploader_in_progress',
            'square_cropping',
            'watermark',
            'watermark_text',
            'watermark_position',
            'watermark_size',
            'watermark_opacity',
            'sharpen_thumbnails',
            'key_value_tags',
            'locations',
            'location_objects',
            'full_size_display_limitation',
            'max_zoom',
            'default_max_zoom',
            'allow_image_adjustments_widget',
            'default_allow_image_adjustments_widget',
            'download_limitation',
            'loop_video',
            'video_file',
            'encoded_video_file',
            'solution',
            'revisions',
            'constellation',
            'is_final',
            'like_count',
            'bookmark_count',
            'comment_count',
            'user_follower_count',
            'uploader_upload_length',
            'uploader_name',
            'iotd_date',
            'is_iotd',
            'is_top_pick',
            'is_top_pick_nomination',
            'is_in_iotd_queue',
            'view_count',
            'average_moon_age',
            'average_moon_illumination',
            'submitted_for_iotd_tp_consideration',
            'detected_language',
        )
