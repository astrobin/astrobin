from rest_framework import serializers

from astrobin_apps_equipment.services import EquipmentItemService


class EquipmentItemSerializer(serializers.ModelSerializer):
    brand_name = serializers.SerializerMethodField(read_only=True)
    variants = serializers.SerializerMethodField(read_only=True)

    def get_brand_name(self, item):
        if item.brand:
            return item.brand.name

        return ""

    def get_variants(self, item):
        ModelClass = self.__class__.Meta.model
        variants = ModelClass.objects.filter(variant_of__pk=item.pk)
        return self.__class__(variants, many=True).data

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
            'variant_of'
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
