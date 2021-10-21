from rest_framework import fields

from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer


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
            'brand',
            'name',
            'image',
        ]
        read_only_fields = ['image']
        abstract = True

    def create(self, validated_data):
        target = validated_data['edit_proposal_target']

        validated_data['edit_proposal_by'] = self.context['request'].user
        validated_data['edit_proposal_ip'] = self.context['request'].META.get("REMOTE_ADDR")

        original_properties = {
            'name': target.name.replace('=', '\='),
            'image': target.image,
        }

        if self.get_original_properties:
            original_properties.update(self.get_original_properties(target))

        validated_data['edit_proposal_original_properties'] = ','.join([
            '%s=%s' % (str(x), y if y else '') for x, y in original_properties.items()
        ])

        return super(EquipmentItemEditProposalSerializer, self).create(validated_data)
