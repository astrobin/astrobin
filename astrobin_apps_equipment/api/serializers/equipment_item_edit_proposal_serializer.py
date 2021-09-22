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
        validated_data['edit_proposal_original_properties'] = \
            'name=%s,image=%s,type=%s,sensor=%s,cooled=%s,max_cooling=%s,back_focus=%s' % (
                target.name.replace('=', '\='),
                target.image if target.image else "",
                target.type,
                str(target.sensor.pk if target.sensor else ""),
                str(target.cooled),
                str(target.max_cooling) if target.max_cooling else "",
                str(target.back_focus) if target.back_focus else ""
            )

        return super(EquipmentItemEditProposalSerializer, self).create(validated_data)
