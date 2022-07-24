from pybb.models import Forum
from rest_framework import serializers


class ForumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forum
        fields = '__all__'
