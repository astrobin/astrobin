from django.contrib.auth.models import User
from django.db.models import Model
from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import PermissionDenied, ValidationError

from astrobin_apps_users.services import UserService
from common.constants import GroupName
from common.exceptions import Conflict


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
    def validate(user: User, attrs):
        if not UserService(user).is_in_group([GroupName.EQUIPMENT_MODERATORS, GroupName.OWN_EQUIPMENT_MIGRATORS]):
            raise PermissionDenied("You don't have permission to create or edit equipment items")

        brand = attrs['brand'] if 'brand' in attrs else None
        variant_of = attrs['variant_of'] if 'variant_of' in attrs else None
        edit_proposal_target = attrs['edit_proposal_target'] if 'edit_proposal_target' in attrs else None

        if variant_of and edit_proposal_target and variant_of == edit_proposal_target:
            raise ValidationError("An item cannot be a variant of itself")

        if brand and variant_of and brand != variant_of.brand:
            raise ValidationError("The variant needs to be in the same brand as the item")

        if not brand and variant_of:
            raise ValidationError("DIY items do not support variants")

        if variant_of and variant_of.variant_of:
            raise ValidationError("Variants do not support variants")

    @staticmethod
    def validate_edit_proposal(user: User, model: Model, attrs):
        from astrobin_apps_equipment.models import EquipmentItem

        target: EquipmentItem = attrs['edit_proposal_target']

        if target.edit_proposal_lock and target.edit_proposal_lock != user:
            raise Conflict()

        already_has_pending = model.objects.filter(
            edit_proposal_review_status__isnull=True, edit_proposal_target=target.pk
        ).exists()
        if already_has_pending:
            raise ValidationError("This item already has a pending edit proposal")

        if 'klass' not in attrs or attrs['klass'] != target.klass:
            raise ValidationError("The klass property must match that of the target item")

        if 'edit_proposal_review_status' in attrs and attrs[
            'edit_proposal_review_status'] is not None:
            raise ValidationError("The edit_proposal_review_status must be null")

        EquipmentItemService.validate_edit_proposal_assignee(user, attrs)

    @staticmethod
    def validate_edit_proposal_assignee(user: User, attrs):
        from astrobin_apps_equipment.models import EquipmentItem

        target: EquipmentItem = attrs['edit_proposal_target']

        if 'edit_proposal_assignee' in attrs and attrs['edit_proposal_assignee'] is not None:
            assignee = attrs['edit_proposal_assignee']
            if assignee == user:
                raise ValidationError("An edit proposal cannot be assigned to its creator")

            if assignee != target.created_by and not assignee.groups.filter(
                    name=GroupName.EQUIPMENT_MODERATORS
            ).exists():
                raise ValidationError("An edit proposal can only be assigned to a moderator or the item's creator")
