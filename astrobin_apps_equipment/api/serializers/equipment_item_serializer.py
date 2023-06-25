from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from astrobin.utils import get_client_country_code
from astrobin_apps_equipment.api.serializers.brand_listing_serializer import BrandListingSerializer
from astrobin_apps_equipment.api.serializers.item_listing_serializer import ItemListingSerializer
from astrobin_apps_equipment.models.equipment_item import EquipmentItem, EquipmentItemReviewerDecision
from astrobin_apps_equipment.services import EquipmentItemService, EquipmentService
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_users.services import UserService
from common.constants import GroupName


class EquipmentItemSerializer(serializers.ModelSerializer):
    brand_name = serializers.SerializerMethodField(read_only=True)
    variants = serializers.SerializerMethodField(read_only=True)
    listings = serializers.SerializerMethodField(read_only=True)
    followed = serializers.SerializerMethodField(read_only=True)
    content_type = serializers.SerializerMethodField(read_only=True)

    def get_brand_name(self, item):
        if item.brand:
            return item.brand.name

        return ""

    def get_variants(self, item):
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user

        ModelClass = self.__class__.Meta.model

        variants = ModelClass.objects.filter(variant_of__pk=item.pk)

        if user and user.is_authenticated:
            if not UserService(user).is_in_group(GroupName.EQUIPMENT_MODERATORS):
                variants = variants.filter(EquipmentItemService.non_moderator_queryset(user))
        else:
            variants = variants.filter(
                reviewer_decision=EquipmentItemReviewerDecision.APPROVED,
                brand__isnull=False,
            )

        return self.__class__(variants, many=True).data

    def get_listings(self, item):
        request = self.context.get("request")

        if request is None:
            return dict()

        country_code = get_client_country_code(request)

        valid_user_subscription = PremiumService(request.user).get_valid_usersubscription()
        allow_full_retailer_integration = PremiumService.allow_full_retailer_integration(valid_user_subscription, None)

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

        return EquipmentItemService(item).is_followed_by_user(request.user)

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
            'image',
            'variant_of',
            'followed',
            'content_type',
        ]
        read_only_fields = ['image']
        abstract = True

    def validate(self, attrs):
        user = self.context['request'].user
        EquipmentItemService.validate(user, attrs)
        return super().validate(attrs)

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        return super(EquipmentItemSerializer, self).create(validated_data)
