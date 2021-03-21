from rest_framework import serializers

from astrobin_apps_groups.models import Group


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            'id',
            'date_created',
            'date_updated',
            'creator',
            'owner',
            'name',
            'description',
            'category',
            'public',
            'moderated',
            'autosubmission',
            'forum',
        ]

    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super(GroupSerializer, self).create(validated_data)
