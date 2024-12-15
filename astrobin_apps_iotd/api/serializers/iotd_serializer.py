from datetime import date, timedelta

from rest_framework import serializers

from astrobin_apps_iotd.models import Iotd


class IotdSerializer(serializers.ModelSerializer):
    date = serializers.DateField(required=False)
    thumbnail = serializers.SerializerMethodField()
    title = serializers.CharField(source='image.title', read_only=True)
    user_display_names = serializers.SerializerMethodField()
    square_cropping = serializers.CharField(source='image.square_cropping', read_only=True)
    w = serializers.IntegerField(source='image.w', read_only=True)
    h = serializers.IntegerField(source='image.h', read_only=True)

    def create(self, validated_data):
        if 'judge' not in validated_data:
            validated_data['judge'] = self.context['request'].user

        day = date.today()
        while self.Meta.model.objects.filter(date=day).exists():
            day = day + timedelta(1)

        validated_data['date'] = day

        return super().create(validated_data)

    def get_thumbnail(self, obj: Iotd) -> str:
        return obj.image.thumbnail('hd', None, sync=True)

    def get_user_display_names(self, obj: Iotd) -> str:
        if obj.image.collaborators.exists():
            return ', '.join(
                [obj.image.user.userprofile.get_display_name()] +
                [
                    collaborator.userprofile.get_display_name() for collaborator in obj.image.collaborators.all()
                ]
            )

        return obj.image.user.userprofile.get_display_name()


    class Meta:
        model = Iotd
        fields = (
            'id',
            'judge',
            'image',
            'square_cropping',
            'w',
            'h',
            'date',
            'thumbnail',
            'title',
            'user_display_names',
        )
