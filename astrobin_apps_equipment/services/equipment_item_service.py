from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import PermissionDenied, ValidationError


class EquipmentItemService:
    item = None

    def __init__(self, item):
        self.item = item

    def get_type(self):
        return self.item.__class__.__name__.lower()

    def get_type_label(self):
        item_type = self.get_type()
        type_map = {
            'telescope': _('Telescope'),
            'camera': _('Camera'),
            'mount': _('Mount'),
            'filter': _('Filter'),
            'accessory': _('Accessory'),
            'software': _('Software'),
        }

        return type_map.get(item_type)

    @staticmethod
    def validate_data(user: User, validated_data):
        if not user.groups.filter(name__in=['equipment_moderators', 'own_equipment_migrators']).exists():
            raise PermissionDenied("You don't have permission to create  or edit equipment items")

        brand = validated_data['brand'] if 'brand' in validated_data else None
        variant_of = validated_data['variant_of'] if 'variant_of' in validated_data else None

        if brand and variant_of and brand != variant_of.brand:
            raise ValidationError("The variant needs to be in the same brand as the item")

        if not brand and variant_of:
            raise ValidationError("DIY items do not support variants")

        if variant_of and variant_of.variant_of:
            raise ValidationError("Variants do not support variants")
