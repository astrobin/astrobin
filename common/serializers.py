from avatar.utils import get_primary_avatar, get_default_avatar_url
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.fields import BooleanField, IntegerField, FloatField, CharField
from rest_framework.relations import PrimaryKeyRelatedField
from subscription.models import UserSubscription, Subscription, Transaction

from astrobin.api2.serializers.location_serializer import LocationSerializer
from astrobin.models import UserProfile, Location
from astrobin_apps_users.services import UserService
from toggleproperties.models import ToggleProperty


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


class TogglePropertySerializer(serializers.ModelSerializer):
    def validate(self, data):
        if data['property_type'] == 'like':
            obj = data['content_type'].get_object_for_this_type(pk=data['object_id'])
            if not UserService(data['user']).can_like(obj):
                raise serializers.ValidationError('User does not have the required permissions to like this object')
        elif data['property_type'] == 'follow':
            pass
        else:
            raise serializers.ValidationError('This property_type is not allowed via the API at the moment')

        return data

    class Meta:
        model = ToggleProperty
        fields = (
            'pk',
            'property_type',
            'user',
            'content_type',
            'object_id',
            'created_on',
        )


class UserProfileSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        return super(serializers.ModelSerializer, self).update(instance, validated_data)

    class Meta:
        model = UserProfile
        exclude = (
            'premium_counter',
            'exclude_from_competitions',
        )


class UserProfileSerializerPrivate(UserProfileSerializer):
    astrobin_index = FloatField(read_only=True, source='get_scores.user_scores_index')
    followers = IntegerField(read_only=True, source='get_scores.user_scores_followers')
    locations = LocationSerializer(many=True, source='location_set')

    def update(self, instance, validated_data):
        locations = validated_data.pop('location_set', [])
        instance = super(UserProfileSerializer, self).update(instance, validated_data)
        instance.location_set.clear()

        for location_data in locations:
            location = Location.objects.get(pk=location_data.get('id'))
            instance.location_set.add(location)

        return instance

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


class PaymentSerializer(serializers.ModelSerializer):
    currency = CharField(read_only=True, source='subscription.currency')

    class Meta:
        model = Transaction
        fields = (
            'id',
            'timestamp',
            'event',
            'amount',
            'currency',
        )
