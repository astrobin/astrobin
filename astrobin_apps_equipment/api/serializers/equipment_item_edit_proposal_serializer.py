from annoying.functions import get_object_or_None
from django.contrib.auth.models import User
from rest_framework import fields
from rest_framework.exceptions import ValidationError

from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from astrobin_apps_equipment.models import EquipmentItem
from common.constants import GroupName
from common.exceptions import Conflict


class EquipmentItemEditProposalSerializer(EquipmentItemSerializer):
    edit_proposal_original_properties = fields.CharField(required=False)

    class Meta(EquipmentItemSerializer.Meta):
        fields = [
            'edit_proposal_original_properties',
            'edit_proposal_target',
            'edit_proposal_by',
            'edit_proposal_created',
            'edit_proposal_updated',
            'edit_proposal_ip',
            'edit_proposal_comment',
            'edit_proposal_reviewed_by',
            'edit_proposal_review_timestamp',
            'edit_proposal_review_ip',
            'edit_proposal_review_comment',
            'edit_proposal_review_status',
            'edit_proposal_assignee',
            'brand',
            'name',
            'community_notes',
            'website',
            'image',
            'variant_of',
        ]
        read_only_fields = ['image']
        abstract = True

    def validate(self, attrs):
        target: EquipmentItem = attrs['edit_proposal_target']

        if target.edit_proposal_lock and target.edit_proposal_lock != self.context.get('request').user:
            raise Conflict()

        already_has_pending = self.Meta.model.objects.filter(
            edit_proposal_review_status__isnull=True, edit_proposal_target=target.pk
        ).exists()
        if already_has_pending:
            raise ValidationError("This item already has a pending edit proposal")

        if 'klass' not in attrs or attrs['klass'] != target.klass:
            raise ValidationError("The klass property must match that of the target item")

        if 'edit_proposal_review_status' in attrs and attrs[
            'edit_proposal_review_status'] is not None:
            raise ValidationError("The edit_proposal_review_status must be null")

        if 'edit_proposal_assignee' in attrs and attrs['edit_proposal_assignee'] is not None:
            assignee = attrs['edit_proposal_assignee']
            if assignee != target.created_by or not assignee.groups.filter(name=GroupName.EQUIPMENT_MODERATORS).exists():
                raise ValidationError("An edit proposal can only be assigned to a moderator or the item's creator")

        return super().validate(attrs)

    def create(self, validated_data):
        validated_data['edit_proposal_by'] = self.context['request'].user
        validated_data['edit_proposal_ip'] = self.context['request'].META.get("REMOTE_ADDR")

        target = validated_data['edit_proposal_target']

        original_properties = {
            'name': target.name.replace('=', '\='),
            'community_notes': target.community_notes.replace('=', '\=') if target.community_notes else None,
            'variant_of': target.variant_of.pk if target.variant_of else None,
            'website': target.website,
            'image': target.image,
        }

        if hasattr(self, 'get_original_properties'):
            original_properties.update(self.get_original_properties(target))

        validated_data['edit_proposal_original_properties'] = ','.join([
            '%s=%s' % (str(x), y if y else '') for x, y in original_properties.items()
        ])

        return super(EquipmentItemEditProposalSerializer, self).create(validated_data)
