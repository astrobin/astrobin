from notification.models import NoticeSetting, NoticeType
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


class NoticeTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoticeType
        fields = [
            'id',
            'label',
            'display',
            'description'
        ]


class NoticeSettingSerializers(serializers.ModelSerializer):
    class Meta:
        model = NoticeSetting
        fields = [
            'id',
            'user',
            'notice_type',
            'medium',
            'send'
        ]
