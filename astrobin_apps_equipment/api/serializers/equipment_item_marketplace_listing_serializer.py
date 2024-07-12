from hitcount.models import HitCount
from rest_framework import serializers

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_read_serializer import \
    EquipmentItemMarketplaceListingLineItemReadSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing
from toggleproperties.models import ToggleProperty


class EquipmentItemMarketplaceListingSerializer(serializers.ModelSerializer):
    user_display_name = serializers.SerializerMethodField(read_only=True)
    user_signup_country = serializers.SerializerMethodField(read_only=True)
    user_last_seen_in_country = serializers.SerializerMethodField(read_only=True)
    line_items = EquipmentItemMarketplaceListingLineItemReadSerializer(many=True, read_only=True)
    # Whether the current user is following the listing
    followed = serializers.SerializerMethodField(read_only=True)
    follower_count = serializers.SerializerMethodField(read_only=True)
    view_count = serializers.SerializerMethodField(read_only=True)
    hitcount_pk = serializers.SerializerMethodField(read_only=True)
    slug = serializers.ReadOnlyField()

    def is_list_view(self) -> bool:
        request = self.context.get('request')
        if request and 'hash' in request.query_params:
            return False
        return isinstance(self.root, serializers.ListSerializer)

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

    def get_user_display_name(self, obj: EquipmentItemMarketplaceListing) -> str:
        return obj.user.userprofile.get_display_name()

    def get_user_signup_country(self, obj: EquipmentItemMarketplaceListing) -> str:
        return obj.user.userprofile.signup_country

    def get_user_last_seen_in_country(self, obj: EquipmentItemMarketplaceListing) -> str:
        return obj.user.userprofile.last_seen_in_country

    def get_followed(self, obj):
        if self.is_list_view():
            return False

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ToggleProperty.objects.toggleproperties_for_object('follow', obj, request.user).exists()
        return False

    def get_follower_count(self, obj):
        if self.is_list_view():
            return None

        return ToggleProperty.objects.toggleproperties_for_object('follow', obj).count()

    def get_view_count(self, obj):
        if self.is_list_view():
            return None

        return HitCount.objects.get_for_object(obj).hits

    def get_hitcount_pk(self, obj):
        if self.is_list_view():
            return None

        return HitCount.objects.get_for_object(obj).pk

    class Meta:
        model = EquipmentItemMarketplaceListing
        fields = '__all__'
        read_only_fields = [
            'id',
            'hash',
            'user',
            'created',
            'updated',
        ]
