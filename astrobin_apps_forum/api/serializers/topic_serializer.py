from pybb.models import Topic
from rest_framework import serializers


class TopicSerializer(serializers.ModelSerializer):
    read = serializers.SerializerMethodField()

    def get_read(self, obj: Topic) -> bool:
        user = self.context['request'].user

        if not user.is_authenticated:
            return False

        return obj.readed_by.filter(pk=self.context['request'].user.pk).exists()

    class Meta:
        model = Topic
        exclude = [
            'readed_by'
        ]
