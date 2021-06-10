from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.http import last_modified
from django.views.decorators.vary import vary_on_cookie
from django_filters.rest_framework import DjangoFilterBackend
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import generics, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer
from subscription.models import Subscription, UserSubscription, Transaction

from astrobin.models import UserProfile
from astrobin_apps_users.services import UserService
from toggleproperties.models import ToggleProperty
from .permissions import ReadOnly
from .serializers import ContentTypeSerializer, UserSerializer, UserProfileSerializer, UserProfileSerializerPrivate, \
    SubscriptionSerializer, UserSubscriptionSerializer, TogglePropertySerializer, PaymentSerializer
from .services.caching_service import CachingService


@method_decorator(cache_page(60 * 60 * 24), name='dispatch')
class ContentTypeList(generics.ListAPIView):
    model = ContentType
    serializer_class = ContentTypeSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = (ReadOnly,)
    pagination_class = None
    filter_fields = ('app_label', 'model',)
    http_method_names = ['get', 'head']
    queryset = ContentType.objects.all()


class ContentTypeDetail(generics.RetrieveAPIView):
    model = ContentType
    serializer_class = ContentTypeSerializer
    permission_classes = (ReadOnly,)
    queryset = ContentType.objects.all()


class UserList(generics.ListAPIView):
    model = User
    serializer_class = UserSerializer
    permission_classes = (ReadOnly,)
    pagination_class = None
    queryset = User.objects.all()


@method_decorator([last_modified(CachingService.get_user_detail_last_modified)], name='dispatch')
class UserDetail(generics.RetrieveAPIView):
    model = User
    serializer_class = UserSerializer
    permission_classes = (ReadOnly,)
    queryset = User.objects.all()


class TogglePropertyList(generics.ListCreateAPIView):
    model = ToggleProperty
    serializer_class = TogglePropertySerializer
    queryset = ToggleProperty.objects.all()
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ['property_type', 'object_id', 'content_type', 'user_id']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TogglePropertyDetail(generics.RetrieveDestroyAPIView):
    model = ToggleProperty
    serializer_class = TogglePropertySerializer
    queryset = ToggleProperty.objects.all()
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]

    def perform_destroy(self, serializer):
        if serializer.user == self.request.user:
            instance = self.get_object()
            is_like = instance.property_type == 'like'
            can_unlike = UserService(self.request.user).can_unlike(serializer.content_object)

            if is_like and not can_unlike:
                raise ValidationError('Cannot remove this like')

            return super(TogglePropertyDetail, self).perform_destroy(instance)

        raise ValidationError('Cannot delete another user\'s toggleproperty')


class UserProfileList(generics.ListAPIView):
    model = UserProfile
    serializer_class = UserProfileSerializer
    permission_classes = (ReadOnly,)
    pagination_class = None
    queryset = UserProfile.objects.all()


class UserProfileDetail(generics.RetrieveAPIView):
    model = UserProfile
    permission_classes = (ReadOnly,)
    queryset = UserProfile.objects.all()

    def get_serializer_class(self):
        profile = self.get_queryset().first()
        if profile.user.pk == self.request.user.pk:
            return UserProfileSerializerPrivate
        return UserProfileSerializer


@method_decorator([last_modified(CachingService.get_current_user_profile_last_modified), vary_on_cookie], name='dispatch')
class CurrentUserProfileDetail(generics.ListAPIView):
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


class UserProfilePartialUpdate(generics.GenericAPIView, mixins.UpdateModelMixin):
    model = UserProfile
    serializer_class = UserProfileSerializerPrivate
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return self.model.objects.filter(user=self.request.user)
        return self.model.objects.none()

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


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


@method_decorator([
    cache_page(600),
    last_modified(CachingService.get_current_user_profile_last_modified),
    vary_on_cookie
], name='dispatch')
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


class PaymentList(generics.ListAPIView):
    model = UserSubscription
    serializer_class = PaymentSerializer
    permission_classes = (ReadOnly,)
    pagination_class = None
    queryset = Transaction.objects.filter(event__in=['one-time payment', 'subscription payment'])
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('user',)

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return self.queryset.filter(user=self.request.user)
        return self.model.objects.none()
