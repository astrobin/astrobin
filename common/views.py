from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics
from rest_framework.filters import DjangoFilterBackend
from subscription.models import Subscription, UserSubscription

from astrobin.models import UserProfile
from .permissions import ReadOnly
from .serializers import ContentTypeSerializer, UserSerializer, UserProfileSerializer, UserProfileSerializerPrivate, \
    SubscriptionSerializer, UserSubscriptionSerializer


@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class ContentTypeList(generics.ListAPIView):
    model = ContentType
    serializer_class = ContentTypeSerializer
    permission_classes = (ReadOnly,)
    pagination_class = None
    filter_fields = ('app_label', 'model',)


class ContentTypeDetail(generics.RetrieveAPIView):
    model = ContentType
    serializer_class = ContentTypeSerializer
    permission_classes = (ReadOnly,)
    queryset = ContentType.objects.all()


class UserList(generics.ListAPIView):
    """
    This view presents a list of all the users in the system.
    """
    model = User
    serializer_class = UserSerializer
    permission_classes = (ReadOnly,)
    pagination_class = None
    queryset = User.objects.all()


class UserDetail(generics.RetrieveAPIView):
    """
    This view presents a instance of one of the users in the system.
    """
    model = User
    serializer_class = UserSerializer
    permission_classes = (ReadOnly,)
    queryset = User.objects.all()


class UserProfileList(generics.ListAPIView):
    """
    This view presents a list of all the user profiles in the system.
    """
    model = UserProfile
    serializer_class = UserProfileSerializer
    permission_classes = (ReadOnly,)
    pagination_class = None
    queryset = UserProfile.objects.all()


class UserProfileDetail(generics.RetrieveAPIView):
    """
    This view presents a instance of one of the user profiles in the system.
    """
    model = UserProfile
    permission_classes = (ReadOnly,)
    queryset = UserProfile.objects.all()

    def get_serializer_class(self):
        profile = self.get_queryset().first()
        if profile.user.pk == self.request.user.pk:
            return UserProfileSerializerPrivate
        return UserProfileSerializer


class CurrentUserProfileDetail(generics.ListAPIView):
    """
    This view retrieves the user currently in the request.
    """
    model = UserProfile
    permission_classes = (ReadOnly,)
    queryset = UserProfile.objects.all()
    pagination_class = None

    def get_serializer_class(self):
        profile = self.get_queryset().first()
        if profile and profile.user == self.request.user:
            return UserProfileSerializerPrivate
        return UserProfileSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return self.queryset.filter(user=self.request.user)
        return self.model.objects.none()


@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class SubscriptionList(generics.ListAPIView):
    model = Subscription
    serializer_class = SubscriptionSerializer
    permission_classes = (ReadOnly,)
    pagination_class = None
    queryset = Subscription.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('category',)


@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class SubscriptionDetail(generics.RetrieveAPIView):
    model = Subscription
    serializer_class = SubscriptionSerializer
    permission_classes = (ReadOnly,)
    queryset = Subscription.objects.all()


class UserSubscriptionList(generics.ListAPIView):
    model = UserSubscription
    serializer_class = UserSubscriptionSerializer
    permission_classes = (ReadOnly,)
    pagination_class = None
    queryset = UserSubscription.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('user',)


class UserSubscriptionDetail(generics.RetrieveAPIView):
    model = UserSubscription
    serializer_class = UserSubscriptionSerializer
    permission_classes = (ReadOnly,)
    queryset = UserSubscription.objects.all()
