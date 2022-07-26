from pybb.models import Topic
from rest_framework import serializers


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = '__all__'
