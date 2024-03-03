from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from astrobin.utils import get_client_country_code
from astrobin_apps_equipment.api.serializers.brand_listing_serializer import BrandListingSerializer
from astrobin_apps_equipment.api.serializers.item_listing_serializer import ItemListingSerializer
from astrobin_apps_equipment.models.equipment_item import EquipmentItem, EquipmentItemReviewerDecision
from astrobin_apps_equipment.services import EquipmentItemService, EquipmentService
from astrobin_apps_premium.services.premium_service import PremiumService
from common.constants import GroupName


class EquipmentItemSerializer(serializers.ModelSerializer):
    brand_name = serializers.SerializerMethodField(read_only=True)
    variants = serializers.SerializerMethodField(read_only=True)
    listings = serializers.SerializerMethodField(read_only=True)
    followed = serializers.SerializerMethodField(read_only=True)
    content_type = serializers.SerializerMethodField(read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Cache some information for the current request.user, which will remain the same for every item being
        # serialized.
        self._user_groups = None
        self._allow_full_retailer_integration = None
        self._followed = None

    def get_user_groups(self, user):
        if self._user_groups is None:
            self._user_groups = set(user.groups.values_list('name', flat=True))
        return self._user_groups

    def get_allow_full_retailer_integration(self, user):
        if self._allow_full_retailer_integration is None:
            valid_user_subscription = PremiumService(user).get_valid_usersubscription()
            self._allow_full_retailer_integration = PremiumService.allow_full_retailer_integration(
                valid_user_subscription, None
            )
        return self._allow_full_retailer_integration

    def get_brand_name(self, item):
        if item.brand:
            return item.brand.name

        return ""

    def get_variants(self, item):
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        allow_unapproved = request and request.GET.get("allow-unapproved", "false") == "true"

        ModelClass = self.__class__.Meta.model
        variants = ModelClass.objects.filter(variant_of__pk=item.pk)

        if user and user.is_authenticated:
            user_groups = self.get_user_groups(user)
            is_equipment_moderator = GroupName.EQUIPMENT_MODERATORS in user_groups
        else:
            is_equipment_moderator = False

        variants = variants.filter(
            EquipmentItemService.non_diy_or_creator_or_moderator_queryset(user, is_equipment_moderator) &
            EquipmentItemService.approved_or_creator_or_moderator_queryset(
                user,
                is_equipment_moderator,
                allow_unapproved
            )
        )

        return self.__class__(variants, many=True).data

    def get_listings(self, item):
        request = self.context.get("request")

        if request is None:
            return dict()

        country_code = get_client_country_code(request)

        allow_full_retailer_integration = self.get_allow_full_retailer_integration(request.user)

        item_listings = EquipmentService.equipment_item_listings(item, country_code)
        brand_listings = EquipmentService.equipment_brand_listings_by_item(item, country_code)
        return dict(
            brand_listings=BrandListingSerializer(brand_listings, many=True).data,
            item_listings=ItemListingSerializer(item_listings, many=True).data,
            allow_full_retailer_integration=allow_full_retailer_integration,
        )

    def get_followed(self, item):
        request = self.context.get("request")

        if request is None or not request.user.is_authenticated:
            return False

        if self._followed is None:
            self._followed = EquipmentItemService(item).is_followed_by_user(request.user)

        return self._followed

    def get_content_type(self, item):
        return ContentType.objects.get_for_model(item).id

    def to_representation(self, item: EquipmentItem):
        ret = super().to_representation(item)

        if item.variant_of:
            if not item.website:
                ret['website'] = item.variant_of.website
            if not item.image:
                ret['image'] = item.variant_of.image.url if item.variant_of.image else None

        return ret

    class Meta:
        fields = [
            'klass',
            'created_by',
            'reviewed_by',
            'reviewed_timestamp',
            'reviewer_decision',
            'reviewer_rejection_reason',
            'reviewer_comment',
            'created',
            'updated',
            'brand',
            'brand_name',
            'name',
            'website',
            'variant_of',
            'followed',
            'content_type',
        ]
        read_only_fields = [
            'image',
            'thumbnail',
        ]
        abstract = True

    def validate(self, attrs):
        user = self.context['request'].user
        EquipmentItemService.validate(user, attrs)
        return super().validate(attrs)

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super(EquipmentItemSerializer, self).create(validated_data)
