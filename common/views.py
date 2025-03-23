from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext
from django.views.decorators.cache import cache_control, cache_page, never_cache
from django.views.decorators.http import last_modified
from django.views.decorators.vary import vary_on_headers
from django_filters.rest_framework import DjangoFilterBackend
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import generics, mixins, parsers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from subscription.models import Subscription, Transaction, UserSubscription

from astrobin.models import Image, UserProfile
from astrobin_apps_images.services import ImageService
from astrobin_apps_users.services import UserService
from toggleproperties.models import ToggleProperty
from .permissions import ReadOnly
from .serializers import (
    ContentTypeSerializer, PaymentSerializer, SubscriptionSerializer, TogglePropertySerializer,
    UserProfileFollowersSerializer, UserProfileFollowingSerializer, UserProfileMutualFollowersSerializer,
    UserProfileSerializer, UserProfileSerializerPrivate,
    UserProfileStatsSerializer,
    UserSerializer,
    UserSubscriptionSerializer,
)
from .services.caching_service import CachingService


def invalidate_avatar_cache(user):
    """
    Aggressively invalidate django-avatar's cache for a specific user.
    This function should be called whenever a user's avatar is changed or deleted.
    """
    import logging
    import time
    logger = logging.getLogger(__name__)
    
    # Update the user profile's updated timestamp for our own cache invalidation
    UserProfile.objects.filter(user=user).update(updated=timezone.now())
    
    # Set a force refresh flag that the serializer will check
    # This helps with browser-side caching issues
    cache.set(f"avatar_force_refresh_{user.id}", int(time.time()), 60*60)  # Cache for up to an hour
    
    try:
        # 1. Use django-avatar's built-in cache invalidation
        from avatar.utils import invalidate_cache
        invalidate_cache(user)
        logger.info(f"Used django-avatar's invalidate_cache for user {user.id}")
        
        # 2. Clear all cached avatar URLs from the cache with all possible size variations
        from avatar.conf import settings as avatar_settings
        
        if avatar_settings.AVATAR_CACHE_ENABLED:
            # Use the default cache
            avatar_cache = cache
                
            # Clear cache for all sizes (standard sizes plus some extra for safety)
            standard_sizes = set(avatar_settings.AVATAR_AUTO_GENERATE_SIZES)
            standard_sizes.add(getattr(avatar_settings, 'AVATAR_DEFAULT_SIZE', 80))
            
            # Add extra common sizes for good measure
            extra_sizes = {30, 40, 50, 60, 100, 150, 200, 250, 300}
            all_sizes = standard_sizes.union(extra_sizes)
            
            for size in all_sizes:
                # Try different cache key formats used by django-avatar
                cache_keys = [
                    f'avatar_{user.id}_{size}',                  # Most common format
                    f'avatar_url_{user.id}_{size}',              # Alternative format
                    f'avatar_{user.username}_{size}',            # Username-based format
                    f'avatar_cached_for_{user.id}_{size}',       # Another possible format
                    f'avatar_url_cached_{user.id}_{size}',       # Another possible format
                ]
                
                for key in cache_keys:
                    avatar_cache.delete(key)
                    logger.info(f"Deleted cache key: {key}")
            
            # Also clear cache for avatar existence check
            avatar_cache.delete(f'avatar_{user.id}_exists')
            avatar_cache.delete(f'avatar_{user.username}_exists')
            
            # Add final cache flush for avatar cache keys that start with the user ID
            # This is a more targeted approach than clearing the entire cache
            avatar_cache_pattern = f"avatar*{user.id}*"
            try:
                # Try to delete cache by pattern if available
                if hasattr(cache, 'delete_pattern'):
                    cache.delete_pattern(avatar_cache_pattern)
                    logger.info(f"Deleted cache pattern: {avatar_cache_pattern}")
            except:
                logger.info(f"Cache backend doesn't support delete_pattern, used individual keys instead")
    except Exception as e:
        logger.exception(f"Error while invalidating avatar cache: {e}")


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
    queryset = User.objects.filter(
        userprofile__deleted__isnull=True,
        userprofile__suspended__isnull=True
    ).prefetch_related(
        'groups',
        'groups__permissions'
    ).all()

    def get_cache_key(self, username):
        return f"api_common_user_list:{username}"

    def list(self, request, *args, **kwargs):
        username = request.GET.get('username')

        if not username:
            return super().list(request, *args, **kwargs)

        cache_key = self.get_cache_key(username)

        # Try to get from cache
        cached_data = cache.get(cache_key)

        try:
            user = UserService.get_case_insensitive(username)
        except User.DoesNotExist:
            return Response(status=404)

        if cached_data:
            cache_timestamp = cached_data.get('timestamp')
            if cache_timestamp and cache_timestamp >= user.userprofile.updated.timestamp():
                return Response([cached_data['data']])

        # Get fresh data
        serialized = self.get_serializer(user).data

        # Cache the fresh data
        cache_data = {
            'data': serialized,
            'timestamp': user.userprofile.updated.timestamp()
        }
        cache.set(cache_key, cache_data)
        return Response([serialized])


@method_decorator(
    [
        last_modified(CachingService.get_user_detail_last_modified),
        cache_control(private=True, no_cache=True),
    ], name='dispatch'
)
class UserDetail(generics.RetrieveAPIView):
    model = User
    serializer_class = UserSerializer
    permission_classes = (ReadOnly,)
    queryset = User.objects.filter(
        userprofile__deleted__isnull=True,
        userprofile__suspended__isnull=True
    ).prefetch_related(
        'groups',
        'groups__permissions'
    ).all()


class UserEmptyTrash(generics.GenericAPIView):
    model = User
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):
        user = self.get_object()

        if user == request.user or request.user.is_superuser:
            UserService(user).empty_trash()
            return Response(status=204)

        raise ValidationError('Cannot empty another user\'s trash')


class TogglePropertyList(generics.ListCreateAPIView):
    model = ToggleProperty
    serializer_class = TogglePropertySerializer
    queryset = ToggleProperty.objects.all()
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = {
        'property_type': ['exact'],
        'content_type': ['exact'],
        'object_id': ['exact', 'in'],
        'user_id': ['exact', 'in']
    }

    def create(self, request, *args, **kwargs):
        existing = ToggleProperty.objects.filter(
            content_type=request.data.get('content_type'),
            object_id=request.data.get('object_id'),
            property_type=request.data.get('property_type'),
            user=request.user
        )

        if existing.exists():
            serializer = self.get_serializer(existing.first())
            return Response(serializer.data, status=200)

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError('This toggle property already exists')


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
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('user',)

    def get_queryset(self) -> QuerySet:
        if 'q' in self.request.query_params:
            q = self.request.query_params.get('q')
            return UserProfile.objects.filter(
                Q(suspended__isnull=True) &
                Q(
                    Q(real_name__icontains=q) |
                    Q(user__username__icontains=q)
                )
            ).distinct()[:20]

        return UserProfile.objects.filter(
            deleted__isnull=True,
            suspended__isnull=True
        )


@method_decorator(
    [
        last_modified(CachingService.get_userprofile_detail_last_modified),
        cache_control(private=True, no_cache=True),
    ], name='dispatch'
)
class UserProfileDetail(generics.RetrieveAPIView):
    model = UserProfile
    permission_classes = (ReadOnly,)
    queryset = UserProfile.objects.filter(
        suspended__isnull=True
    )

    def get_serializer_class(self):
        profile = self.get_queryset().first()
        if profile.user.pk == self.request.user.pk:
            return UserProfileSerializerPrivate
        return UserProfileSerializer


@method_decorator(
    [
        last_modified(CachingService.get_userprofile_detail_last_modified),
        cache_control(private=True, no_cache=True),
    ], name='dispatch'
)
class UserProfileStats(generics.RetrieveAPIView):
    model = UserProfile
    permission_classes = (ReadOnly,)
    queryset = UserProfile.objects.filter(
        suspended__isnull=True
    )

    def get_serializer_class(self):
        return UserProfileStatsSerializer


class UserProfileFollowers(generics.RetrieveAPIView):
    model = UserProfile
    permission_classes = (ReadOnly,)
    queryset = UserProfile.objects.filter(
        suspended__isnull=True
    )

    def get_serializer_class(self):
        return UserProfileFollowersSerializer


class UserProfileFollowing(generics.RetrieveAPIView):
    model = UserProfile
    permission_classes = (ReadOnly,)
    queryset = UserProfile.objects.all()

    def get_serializer_class(self):
        return UserProfileFollowingSerializer


class UserProfileMutualFollowers(generics.RetrieveAPIView):
    model = UserProfile
    permission_classes = (ReadOnly,)
    queryset = UserProfile.objects.all()

    def get_serializer_class(self):
        return UserProfileMutualFollowersSerializer


@method_decorator(never_cache, name='dispatch')
class UserProfileChangeGalleryHeader(generics.UpdateAPIView):
    model = UserProfile
    permission_classes = [IsAuthenticated]
    queryset = UserProfile.objects.filter(
        suspended__isnull=True
    )

    def update(self, request, *args, **kwargs):
        profile: UserProfile = self.get_object()

        if profile.user != request.user:
            self.permission_denied(request, message='Cannot change another user\'s gallery header')

        image_id: str = kwargs.get('image_id')
        image: Image = ImageService.get_object(image_id, Image.objects_including_wip_plain)

        if not image:
            return Response(status=404, data={'detail': 'Image not found'})

        if image.user != request.user:
            self.permission_denied(request, message='Cannot use another user\'s image as gallery header')

        thumbnail: str = image.thumbnail('hd', None, sync=True)
        profile.gallery_header_image = thumbnail
        profile.save()

        return Response(UserProfileSerializerPrivate(profile, context=dict(request=request)).data)


@method_decorator(
    [
        last_modified(CachingService.get_current_user_profile_last_modified),
        cache_control(private=True, no_cache=True),
        vary_on_headers('Cookie', 'Authorization')
    ], name='dispatch'
)
class CurrentUserProfileDetail(generics.ListAPIView):
    model = UserProfile
    permission_classes = (ReadOnly,)
    queryset = UserProfile.objects.filter(
        suspended__isnull=True
    )
    pagination_class = None

    def get_serializer_class(self):
        profile = self.get_queryset().first()
        if profile and profile.user == self.request.user:
            return UserProfileSerializerPrivate
        return UserProfileSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        return self.model.objects.none()


class UserProfilePartialUpdate(generics.GenericAPIView, mixins.UpdateModelMixin):
    model = UserProfile
    serializer_class = UserProfileSerializerPrivate
    permission_classes = [IsAuthenticated]
    parser_classes = [CamelCaseJSONParser]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.model.objects.filter(user=self.request.user, suspended__isnull=True)
        return self.model.objects.none()

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class UserProfileShadowBanView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(never_cache)
    def post(self, request, pk):
        if int(pk) == request.user.pk:
            return Response(
                {'detail': 'Cannot shadow-ban yourself'},
                status=HTTP_403_FORBIDDEN
            )

        profile_to_ban = get_object_or_404(UserProfile, user_id=pk)
        requester_profile = request.user.userprofile

        if profile_to_ban in requester_profile.shadow_bans.all():
            return Response(
                {'detail': 'User is already shadow-banned'},
                status=HTTP_400_BAD_REQUEST
            )

        requester_profile.shadow_bans.add(profile_to_ban)

        return Response(
            {
                'message': gettext(
                    "You have shadow-banned %s. They will not be notified about it."
                ) % profile_to_ban.get_display_name()
            }, status=HTTP_200_OK
        )


class UserProfileRemoveShadowBanView(GenericAPIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(never_cache)
    def post(self, request, pk):
        if int(pk) == request.user.pk:
            return Response(
                {'detail': 'Cannot remove shadow-ban from yourself'},
                status=HTTP_403_FORBIDDEN
            )

        profile_to_unban = get_object_or_404(UserProfile, user_id=pk)
        requester_profile = request.user.userprofile

        if profile_to_unban not in requester_profile.shadow_bans.all():
            return Response(
                {'detail': 'User is not shadow-banned'},
                status=HTTP_400_BAD_REQUEST
            )

        requester_profile.shadow_bans.remove(profile_to_unban)

        return Response(
            {
                'message': gettext(
                    "You have removed your shadow-ban for %s. They will not be notified about it."
                ) % profile_to_unban.get_display_name()
            }, status=HTTP_200_OK
        )

class SubscriptionList(generics.ListAPIView):
    model = Subscription
    serializer_class = SubscriptionSerializer
    permission_classes = (ReadOnly,)
    pagination_class = None
    queryset = Subscription.objects.all().select_related('group').prefetch_related('group__permissions')
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('category',)


class SubscriptionDetail(generics.RetrieveAPIView):
    model = Subscription
    serializer_class = SubscriptionSerializer
    permission_classes = (ReadOnly,)
    queryset = Subscription.objects.all().select_related('group').prefetch_related('group__permissions')


@method_decorator(
    [
        last_modified(CachingService.get_current_user_profile_last_modified),
        cache_control(private=True, no_cache=True),
        vary_on_headers('Cookie', 'Authorization')
    ], name='dispatch'
)
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
    model = Transaction
    serializer_class = PaymentSerializer
    permission_classes = (ReadOnly,)
    pagination_class = None
    queryset = Transaction.objects.filter(event__in=['one-time payment', 'subscription payment'])
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('user',)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        return self.model.objects.none()


class UserAvatarAdd(generics.GenericAPIView):
    """Add a new avatar for the user."""
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]  # Only multipart and form parsers
    MAX_AVATAR_SIZE = 10 * 1024 * 1024  # 10 MB in bytes

    def post(self, request):
        return self._handle_request(request)
        
    def put(self, request):
        return self._handle_request(request)
        
    def _handle_request(self, request):
        from avatar.models import Avatar
        from avatar.signals import avatar_updated
        import logging
        import uuid
        from io import BytesIO
        from PIL import Image as PILImage
        
        logger = logging.getLogger(__name__)
        
        if 'file' not in request.FILES:
            return Response({'detail': 'No avatar file provided'}, status=400)
        
        avatar_file = request.FILES['file']
        
        if avatar_file.size > self.MAX_AVATAR_SIZE:
            return Response({
                'errors': {
                    'file': [f'Avatar file too large. Maximum size is 10 MB.']
                }
            }, status=400)
        
        try:
            logger.info(
                f"Avatar upload - File info: "
                f"name={avatar_file.name}, size={avatar_file.size}, content_type={avatar_file.content_type}"
            )
            
            # Try to validate the image using PIL directly
            try:
                # Create a copy of the file in memory
                file_copy = BytesIO(avatar_file.read())
                # Reset the file pointer to the beginning for later use
                avatar_file.seek(0)
                
                # Try to open the image with PIL
                img = PILImage.open(file_copy)
                img.verify()  # Verify it's a valid image
                
                # Get the image format for the filename extension
                img_format = img.format.lower() if img.format else 'jpeg'
                logger.info(f"Image verified with PIL: format={img_format}, size={img.size}, mode={img.mode}")
            except Exception as img_error:
                logger.warning(f"PIL image verification failed: {img_error}")
                return Response({
                    'errors': {
                        'file': ['The uploaded file is not a valid image. Please try a different file.']
                    }
                }, status=400)
                
            avatar = Avatar(user=request.user, primary=True)
            
            # Generate a unique filename with the correct extension
            filename = f"avatar_{uuid.uuid4()}.{img_format}"
            
            # Save the file directly
            avatar.avatar.save(filename, avatar_file)
            avatar.save()
            
            # Set primary status
            Avatar.objects.filter(user=request.user, primary=True).exclude(pk=avatar.pk).update(primary=False)

            # Send signal
            avatar_updated.send(sender=Avatar, user=request.user, avatar=avatar)

            # Invalidate the avatar cache
            invalidate_avatar_cache(request.user)
            
            # Get the properly sized square avatar URL (200px)
            from avatar.templatetags.avatar_tags import avatar_url
            sized_avatar_url = avatar_url(request.user, 200)
            
            return Response({
                'success': True,
                'avatar_url': sized_avatar_url,
            }, status=201)
                
        except Exception as e:
            logger.exception(f"Error uploading avatar: {e}")
            return Response({
                'errors': {
                    'file': [f'An error occurred while processing the avatar: {str(e)}']
                }
            }, status=500)


class UserAvatarDelete(generics.GenericAPIView):
    """Delete a specific avatar by ID."""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        return self._handle_request(request, pk)
        
    def delete(self, request, pk):
        return self._handle_request(request, pk)
        
    def _handle_request(self, request, pk):
        from avatar.models import Avatar
        from avatar.signals import avatar_deleted
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"Attempting to delete avatar with ID {pk} for user {request.user.id}")
        
        try:
            # Try to get the specific avatar
            try:
                avatar = Avatar.objects.get(id=pk, user=request.user)
            except Avatar.DoesNotExist:
                return Response({'detail': 'Avatar not found'}, status=404)
            
            # Get some info for logging
            avatar_id = avatar.id
            avatar_path = avatar.avatar.name if avatar.avatar else None
            logger.info(f"Found avatar id={avatar_id}, path={avatar_path}")
            
            # Check if this is the primary avatar
            is_primary = avatar.primary
            
            # Send signal
            avatar_deleted.send(sender=Avatar, user=request.user, avatar=avatar)
            
            # Delete the file if it exists
            if avatar.avatar:
                try:
                    logger.info(f"Deleting avatar file: {avatar.avatar.name}")
                    avatar.avatar.delete(save=False)
                except Exception as file_error:
                    logger.error(f"Error deleting avatar file: {file_error}")
                    # Continue anyway - we want to delete the DB record even if file deletion fails
            
            # Delete the database record
            logger.info(f"Deleting avatar record: id={avatar_id}")
            avatar.delete()
            logger.info(f"Avatar {avatar_id} deleted successfully")
            
            # If we deleted the primary avatar, set another one as primary if available
            if is_primary:
                remaining_avatars = Avatar.objects.filter(user=request.user)
                if remaining_avatars.exists():
                    new_primary = remaining_avatars.first()
                    new_primary.primary = True
                    new_primary.save()
                    logger.info(f"Set avatar id={new_primary.id} as new primary")
            
            # Invalidate the avatar cache
            invalidate_avatar_cache(request.user)
            
            # Get the default avatar URL to return (either new primary or default image)
            from avatar.templatetags.avatar_tags import avatar_url
            from avatar.conf import settings as avatar_settings
            default_url = avatar_url(request.user, avatar_settings.AVATAR_DEFAULT_SIZE)
            
            return Response({
                'success': True, 
                'message': f'Avatar {avatar_id} deleted successfully',
                'default_avatar_url': default_url
            }, status=200)
                
        except Exception as e:
            logger.exception(f"Error deleting avatar: {e}")
            return Response({
                'success': False,
                'error': f'Failed to delete avatar: {str(e)}'
            }, status=500)
