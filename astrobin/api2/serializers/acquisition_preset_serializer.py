from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class AcquisitionPresetSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True
        read_only_fields = ['id', 'saved_on', 'user']

    def create(self, validated_data):
        user = self.context['request'].user
        name = validated_data['name']

        if self.Meta.model.objects.filter(user=user, name=name).exists():
            raise ValidationError(f'User {user.username} already has a preset with name {name}.')

        validated_data['user'] = user
        return super().create(validated_data)
