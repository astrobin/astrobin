from persistent_messages.models import Message
from rest_framework import serializers


class NotificationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Message
        fields = [
            'id',
            'user',
            'from_user',
            'subject',
            'message',
            'level',
            'extra_tags',
            'created',
            'modified',
            'read',
            'expires',
            'close_timeout',
        ]
