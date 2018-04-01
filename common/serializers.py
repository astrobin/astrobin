# Django
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

# Third party apps
from avatar.utils import get_primary_avatar, get_default_avatar_url
from rest_framework import serializers

# AstroBin
from astrobin.models import UserProfile


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = (
            'id',
            'app_label',
            'model',
        )


class AvatarField(serializers.Field):
    def to_representation(self, obj):
        avatar = get_primary_avatar(obj, 40)
        if avatar is None:
            return get_default_avatar_url()

        return avatar.get_absolute_url()


class UserSerializer(serializers.ModelSerializer):
    avatar = AvatarField(source='*')

    class Meta:
        model = User
        fields = ('username', 'userprofile', 'avatar')


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('real_name',)

