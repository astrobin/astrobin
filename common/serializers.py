# Django
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

# Third party apps
from avatar.utils import get_primary_avatar, get_default_avatar_url
from rest_framework import serializers

# AstroBin
from rest_framework.fields import BooleanField
from rest_framework.relations import PrimaryKeyRelatedField
from subscription.models import UserSubscription, Subscription

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
    userprofile = PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = User
        exclude = ('password', 'email', 'last_name')
        depth = 1


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        exclude = (
            'premium_counter',
            'exclude_from_competitions',
        )


class UserProfileSerializerPrivate(UserProfileSerializer):
    class Meta(UserProfileSerializer.Meta):
        exclude = ()


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'
        depth = 1


class UserSubscriptionSerializer(serializers.ModelSerializer):
    valid = BooleanField()

    class Meta:
        model = UserSubscription
        fields = '__all__'
