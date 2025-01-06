# -*- coding: utf-8 -*-
import logging
from decimal import InvalidOperation
from typing import Optional

import simplejson
from annoying.functions import get_object_or_None
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import Count, OuterRef, Q, QuerySet, Subquery, Value
from django.db.models.functions import Concat
from django.utils.translation import gettext_lazy
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.viewsets import GenericViewSet

from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.models import Collection, DeepSky_Acquisition, Image, SolarSystem_Acquisition, UserProfile
from astrobin_apps_equipment.models import Filter
from astrobin_apps_images.api.filters import ImageFilter
from astrobin_apps_images.api.permissions import IsImageOwnerOrReadOnly
from astrobin_apps_images.api.serializers import ImageSerializer, ImageSerializerSkipThumbnails
from astrobin_apps_images.api.serializers.image_serializer_gallery import ImageSerializerGallery
from astrobin_apps_images.api.serializers.image_serializer_trash import ImageSerializerTrash
from astrobin_apps_images.models import KeyValueTag
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_iotd.templatetags.astrobin_apps_iotd_tags import humanize_may_not_submit_to_iotd_tp_process_reason
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_users.services import UserService
from common.permissions import IsSuperUser, or_permission
from toggleproperties.models import ToggleProperty

logger = logging.getLogger(__name__)


class ImageViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet
):
    queryset = Image.objects_including_wip.all()
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    filter_class = ImageFilter
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        or_permission(IsImageOwnerOrReadOnly, IsSuperUser)
    ]
    http_method_names = ['get', 'head', 'put', 'patch', 'delete']
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'images'

    user: Optional[User] = None
    menu: Optional[str] = None
    active: Optional[str] = None
    sorted_queryset: Optional[QuerySet] = None

    def _prepare_equipment_data(self, request):
        data = {}

        for klass in ImageService.get_equipment_classes():
            try:
                data[klass[0]] = request.data.pop(klass[0])
            except KeyError:
                data[klass[0]] = []

        return data

    def _update_equipment(self, data, instance: Image):
        for klass in ImageService.get_equipment_classes():
            # Get the current set of related objects
            current_objs = set(getattr(instance, klass[0]).all())

            # New objects to be linked
            new_objs = set()
            for item in data[klass[0]]:
                obj = get_object_or_None(klass[1], id=item if type(item) == int else item.get('id'))
                if obj:
                    new_objs.add(obj)

            # Determine objects to add (in new_objs but not in current_objs)
            objs_to_add = new_objs - current_objs

            # Determine objects to remove (in current_objs but not in new_objs)
            objs_to_remove = current_objs - new_objs

            # Update the m2m relationship
            m2m_relation = getattr(instance, klass[0])
            for obj in objs_to_add:
                try:
                    m2m_relation.add(obj)
                except IntegrityError:
                    pass
            for obj in objs_to_remove:
                m2m_relation.remove(obj)

    def _update_acquisition(self, request, instance: Image):
        DeepSky_Acquisition.objects.filter(image=instance).delete()
        deep_sky_decimal_fields = ['duration', 'gain', 'f_number', 'bortle', 'mean_sqm', 'mean_fwhm', 'temperature']
        solar_system_decimal_fields = ['fps', 'exposure_per_frame', 'gain', 'cmi', 'cmii', 'cmiii']

        for item in request.data.get('deep_sky_acquisitions'):
            for field in deep_sky_decimal_fields:
                if item.get(field) == '':
                    item[field] = None

            if item.get('bortle') == '':
                item['bortle'] = None

            filter_2 = item.get('filter_2')

            if isinstance(filter_2, int):
                item['filter_2'] = get_object_or_None(Filter, id=filter_2)
            else:
                filter_: Optional[Filter] = Filter.objects.annotate(
                    full_name=Concat('brand__name', Value(' '), 'name')
                ).filter(
                    full_name=filter_2
                ).first()
                if filter_:
                    item['filter_2'] = filter_.pk

            data = dict(image=instance, **item)

            if 'id' in data:
                del data['id']
            try:
                DeepSky_Acquisition.objects.create(**data)
            except ValueError as e:
                data_str = simplejson.dumps(data, default=str)
                logger.error(f"Error creating DeepSky_Acquisition: {e}. Data: {data_str}")
            except InvalidOperation as e:
                data_str = simplejson.dumps(data, default=str)
                logger.error(f"Error creating DeepSky_Acquisition: {e}. Data: {data_str}")
            except Exception as e:
                data_str = simplejson.dumps(data, default=str)
                logger.error(f"Error creating DeepSky_Acquisition: {e}. Data: {data_str}")
                raise e

        if 'solar_system_acquisitions' in request.data and len(request.data.get('solar_system_acquisitions')) > 1:
            raise ValidationError(gettext_lazy("Only one video-based acquisition is allowed per image."))

        SolarSystem_Acquisition.objects.filter(image=instance).delete()
        for item in request.data.get('solar_system_acquisitions'):
            for field in solar_system_decimal_fields:
                if item.get(field) == '':
                    item[field] = None

            data = dict(image=instance, **item)
            if 'id' in data:
                del data['id']
            try:
                SolarSystem_Acquisition.objects.create(**data)
            except Exception as e:
                data_str = simplejson.dumps(data, default=str)
                logger.error(f"Error creating SolarSystem_Acquisition: {e}. Data: {data_str}")
                raise e

    def get_serializer_class(self):
        if (
                'trash' in self.request.query_params and
                self.request.query_params.get('trash').lower() == 'true'
        ):
            return ImageSerializerTrash

        if (
                'gallery-serializer' in self.request.query_params and
                self.request.query_params.get('gallery-serializer').lower() in ('true', '1')
        ):
            return ImageSerializerGallery

        if (
                'skip-thumbnails' in self.request.query_params and
                self.request.query_params.get('skip-thumbnails').lower() in ('true', '1')
        ):
            return ImageSerializerSkipThumbnails

        return ImageSerializer

    def get_queryset(self):
        # Having a hash in the request means we want to retrieve a single image by hash. This should work even if the
        # image is in the staging area, so we act like the retrieval method. This makes the ImageFilter 'hash' field
        # redundant, but we keep it for consistency.
        if 'hash' in self.request.query_params:
            return Image.objects_including_wip.filter(
                hash=self.request.query_params.get('hash'),
                user__userprofile__suspended__isnull=True
            ).exclude(
                moderator_decision=ModeratorDecision.REJECTED
            )

        if 'pk' in self.kwargs:
            return Image.objects_including_wip.filter(
                pk=self.kwargs['pk'],
                user__userprofile__suspended__isnull=True,
            ).exclude(
                moderator_decision=ModeratorDecision.REJECTED
            )

        if self.sorted_queryset is not None:
            queryset = self.sorted_queryset
        else:
            queryset = Image.objects.all()

        if self.request.query_params.get('user'):
            truism = ['1', 'true', 'yes']

            has_deep_sky_acquisitions_filter = self.request.GET.get('has-deepsky-acquisitions')
            if has_deep_sky_acquisitions_filter and has_deep_sky_acquisitions_filter.lower() in truism:
                queryset = queryset.annotate(
                    num_deepsky_acquisitions=Count('acquisition__deepsky_acquisition')
                ).filter(
                    num_deepsky_acquisitions__gt=0
                )

            has_solar_system_acquisitions_filter = self.request.GET.get('has-solarsystem-acquisitions')
            if has_solar_system_acquisitions_filter and has_solar_system_acquisitions_filter.lower() in truism:
                queryset = queryset.annotate(
                    num_solarsystem_acquisitions=Count('acquisition__solarsystem_acquisition')
                ).filter(
                    num_solarsystem_acquisitions__gt=0
                )

            collection_id = self.request.query_params.get('collection')
            if collection_id:
                try:
                    collection = Collection.objects.get(pk=collection_id)
                except Collection.DoesNotExist:
                    return Image.objects.none()

                # If the collection has an order_by_tag, sort images by that tag
                if collection.order_by_tag:
                    tag_key = collection.order_by_tag

                    # Subquery to get the tag value for each image
                    tag_value_subquery = KeyValueTag.objects.filter(
                        image=OuterRef('pk'),
                        key=tag_key
                    ).values('value')[:1]

                    # Annotate queryset with the tag value and order by it
                    queryset = queryset.annotate(
                        tag_value=Subquery(tag_value_subquery)
                    ).filter(
                        collections=collection
                    ).order_by('tag_value')
                else:
                    queryset = queryset.filter(collections=collection)

            return queryset

        return queryset.filter(
            is_wip=False,
            user__userprofile__suspended__isnull=True
        ).exclude(
            moderator_decision=ModeratorDecision.REJECTED
        )

    def list(self, request, *args, **kwargs):
        # Validate the request parameters
        validation_response = self._validate_list_request(request)
        if validation_response:
            return validation_response

        if 'hash' in request.query_params:
            hash: str = request.query_params.get('hash')
            image: Image = get_object_or_None(
                Image.objects_including_wip_plain,
                hash=hash,
                user__userprofile__suspended__isnull=True
            )
            if not image:
                return Response(status=HTTP_404_NOT_FOUND)

            cache_key: str = f'api_image_{hash}_{request.query_params.get("skip-thumbnails", False)}'
            cached_data = cache.get(cache_key)

            if cached_data:
                cached_timestamp = cached_data.get('timestamp')
                if cached_timestamp and cached_timestamp >= image.updated.timestamp():
                    return Response(cached_data.get('data'))

            # Get fresh data
            serialized = self.get_serializer(image).data
            cache_data = {
                'data': {
                    'count': 1,
                    'next': None,
                    'prev': None,
                    'results': [serialized]
                },
                'timestamp': image.updated.timestamp()
            }
            cache.set(cache_key, cache_data, 3600)
            return Response(cache_data.get('data'))

        if 'user' in request.query_params:
            # Get sorted queryset and extra data
            sorted_queryset, menu, active = self._get_sorted_queryset_and_extra_data(request)
            self.menu = menu
            self.active = active

            if 'ordering' in request.query_params:
                ordering = request.query_params.get('ordering')
                ordering_map = {
                    'likes': '-like_count',
                    'bookmarks': '-bookmark_count',
                    'comments': '-comment_count',
                }

                if ordering not in (
                        'likes',
                        'bookmarks',
                        'comments',
                ):
                    return Response(
                        "Invalid ordering parameter.",
                        status=HTTP_400_BAD_REQUEST
                    )

                sorted_queryset = sorted_queryset.order_by(ordering_map[ordering])

            self.sorted_queryset = sorted_queryset

            # Proceed with the default list behavior
            response = super().list(request, *args, **kwargs)

            # Inject 'menu' and 'active' into the paginated response
            if self.paginator and hasattr(response, 'data'):
                response.data['menu'] = self.menu
                response.data['active'] = self.active
            else:
                # If not paginated, add 'menu' and 'active' to the response
                response = Response(
                    {
                        'menu': self.menu,
                        'active': self.active,
                        'results': response.data
                    }, status=response.status_code
                )

            return response

        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        # Retrieving an image by PK should work even if the image is in the staging area.
        try:
            instance: Image = get_object_or_None(self.queryset, pk=kwargs['pk'])
        except ValueError:
            return Response(status=HTTP_400_BAD_REQUEST, data={'detail': 'Invalid image ID'})

        if not instance:
            return Response(status=HTTP_404_NOT_FOUND)

        if instance.user.userprofile.suspended:
            return Response(status=HTTP_400_BAD_REQUEST, data={'detail': 'User is suspended'})

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        equipment_data = self._prepare_equipment_data(request)

        response: Response = super().update(request, *args, **kwargs)
        instance: Image = self.get_object()

        self._update_equipment(equipment_data, instance)
        self._update_acquisition(request, instance)

        return response

    def perform_destroy(self, instance):
        from astrobin.tasks import invalidate_all_image_thumbnails
        invalidate_all_image_thumbnails.delay(instance.pk)
        return super().perform_destroy(instance)

    @action(detail=False, methods=['get'], url_path='public-images-count')
    def public_images_count(self, request):
        if 'user' not in request.GET:
            return Response("'user' argument is required", HTTP_400_BAD_REQUEST)

        user_id = request.GET.get('user')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(f"User with id {user_id} not found", HTTP_404_NOT_FOUND)

        count = Image.objects_including_wip.filter(user=user).count()

        return Response(count, HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='video-encoding-progress')
    def video_encoding_progress(self, request, pk=None):
        content_type = ContentType.objects.get_for_model(Image)

        value = cache.get(f"video-encoding-progress-{content_type.pk}-{pk}")

        return Response(value, HTTP_200_OK)

    @action(detail=True, methods=['put'], url_path='publish')
    def publish(self, request, pk=None):
        image = self.get_object()

        if image.is_wip:
            image.skip_notifications = self.request.data.get('skip_notifications', False)
            image.skip_activity_stream = self.request.data.get('skip_activity_stream', False)
            ImageService(image).promote_to_public_area(image.skip_notifications, image.skip_activity_stream)
            image.save()

        return Response(status=HTTP_200_OK)

    @action(detail=True, methods=['put'], url_path='unpublish')
    def unpublish(self, request, pk=None):
        image = self.get_object()

        if not image.is_wip:
            ImageService(image).demote_to_staging_area()
            image.save()

        return Response(status=HTTP_200_OK)

    @action(detail=True, methods=['put'], url_path='mark-as-final')
    def mark_as_final(self, request, pk=None):
        image = self.get_object()

        ImageService(image).mark_as_final(request.data.get('revision_label', '0'))

        return Response(status=HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='delete-original')
    def delete_original(self, request, pk=None):
        image = self.get_object()

        revisions = ImageService(image).get_revisions()
        if not revisions.exists():
            return Response(status=HTTP_400_BAD_REQUEST)

        ImageService(image).delete_original()

        serializer = self.get_serializer(image)
        return Response(serializer.data, HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='delete-uncompressed-source-file')
    def delete_uncompressed_source_file(self, request, pk=None):
        image = self.get_object()

        image.uncompressed_source_file.delete(save=False)
        image.save(keep_deleted=True)

        serializer = self.get_serializer(image)
        return Response(serializer.data, HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='may-submit-for-iotd-tp-consideration')
    def may_submit_for_iotd_tp_consideration(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(False, HTTP_200_OK)

        image: Image = self.get_object()
        iotd_service: IotdService = IotdService()
        user_profile: UserProfile = request.user.userprofile
        user_profile_agreed = user_profile.agreed_to_iotd_tp_rules_and_guidelines

        may, reason = iotd_service.may_submit_to_iotd_tp_process(
            request.user,
            image,
            user_profile_agreed
        )

        response = {
            'may': may,
            'reason': reason,
            'humanizedReason': humanize_may_not_submit_to_iotd_tp_process_reason(reason)
        }

        return Response(response, HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='submit-for-iotd-tp-consideration')
    def submit_for_iotd_tp_consideration(self, request, pk=None):
        image: Image = self.get_object()
        iotd_service: IotdService = IotdService()
        request_agreed = request.data.get('agreed_to_iotd_tp_rules_and_guidelines', None)

        if request_agreed is not True:
            return Response({'reason': 'agreed_to_iotd_tp_rules_and_guidelines is required'}, HTTP_400_BAD_REQUEST)

        may, _ = iotd_service.submit_to_iotd_tp_process(request.user, image)

        if not may:
            return Response({'reason': 'Image does not meet the requirements'}, HTTP_400_BAD_REQUEST)

        image.refresh_from_db()
        serializer = self.get_serializer(image)
        return Response(serializer.data, HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='accept-collaborator-request')
    def accept_collaborator_request(self, request, pk=None):
        image: Image = self.get_object()
        collaborator_id = request.data.get('user_id', None)

        if collaborator_id is None:
            return Response("user_id not provided", HTTP_400_BAD_REQUEST)

        collaborator = get_object_or_None(User, id=collaborator_id)

        if collaborator is None:
            return Response("User not found", HTTP_404_NOT_FOUND)

        try:
            ImageService(image).accept_collaborator_request(collaborator)
        except Exception as e:
            return Response(str(e), HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(image)
        return Response(serializer.data, HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='deny-collaborator-request')
    def deny_collaborator_request(self, request, pk=None):
        image: Image = self.get_object()
        collaborator_id = request.data.get('user_id', None)

        if collaborator_id is None:
            return Response("user_id not provided", HTTP_400_BAD_REQUEST)

        collaborator = get_object_or_None(User, id=collaborator_id)

        if collaborator is None:
            return Response("User not found", HTTP_404_NOT_FOUND)

        try:
            ImageService(image).deny_collaborator_request(collaborator)
        except Exception as e:
            return Response(str(e), HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(image)
        return Response(serializer.data, HTTP_200_OK)

    @action(detail=True, methods=['patch'], url_path='remove-collaborator')
    def remove_collaborator(self, request, pk=None):
        image: Image = self.get_object()
        collaborator_id = request.data.get('user_id', None)

        if collaborator_id is None:
            return Response("user_id not provided", HTTP_400_BAD_REQUEST)

        collaborator = get_object_or_None(User, id=collaborator_id)

        if collaborator is None:
            return Response("User not found", HTTP_404_NOT_FOUND)

        try:
            ImageService(image).remove_collaborator(request.user, collaborator)
        except Exception as e:
            return Response(str(e), HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(image)
        return Response(serializer.data, HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def undelete(self, request, pk=None):
        try:
            image: Image = Image.deleted_objects.get(pk=pk)
        except Image.DoesNotExist:
            return Response("Image not found", HTTP_404_NOT_FOUND)

        if not request.user.is_authenticated:
            return Response("Authentication required", HTTP_401_UNAUTHORIZED)

        if not request.user.is_superuser and image.user != request.user:
            return Response("Permission denied", HTTP_403_FORBIDDEN)

        valid_usersubscription = PremiumService(request.user).get_valid_usersubscription()
        if not PremiumService.is_any_ultimate(valid_usersubscription):
            return Response("Permission denied", HTTP_403_FORBIDDEN)

        image.undelete()
        serializer = self.get_serializer(image)
        return Response(serializer.data, HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='users-who-like')
    def users_who_like(self, request, pk=None):
        image = self.get_object()
        content_type = ContentType.objects.get_for_model(Image)

        # First query the specific ToggleProperties we want
        properties = ToggleProperty.objects.filter(
            content_type=content_type,
            object_id=image.pk,
            property_type='like'
        ).select_related('user', 'user__userprofile')

        # Then order these by timestamp
        properties = properties.order_by('-created_on')

        if 'users-who-like-q' in request.query_params:
            q = request.query_params.get('users-who-like-q')
            properties = properties.filter(
                Q(user__username__icontains=q) |
                Q(user__userprofile__real_name__icontains=q)
            )

        return Response(
            [
                {
                    'userId': prop.user.pk,
                    'username': prop.user.username,
                    'displayName': prop.user.userprofile.get_display_name(),
                    'timestamp': prop.created_on,
                } for prop in properties
            ],
            HTTP_200_OK
        )

    @action(detail=True, methods=['get'], url_path='users-who-bookmarked')
    def users_who_bookmarked(self, request, pk=None):
        image = self.get_object()
        content_type = ContentType.objects.get_for_model(Image)

        # First query the specific ToggleProperties we want
        properties = ToggleProperty.objects.filter(
            content_type=content_type,
            object_id=image.pk,
            property_type='bookmarked'
        ).select_related('user', 'user__userprofile')

        # Then order these by timestamp
        properties = properties.order_by('-created_on')

        if 'users-who-bookmarked-q' in request.query_params:
            q = request.query_params.get('users-who-bookmarked-q')
            properties = properties.filter(
                Q(user__username__icontains=q) |
                Q(user__userprofile__real_name__icontains=q)
            )

        return Response(
            [
                {
                    'userId': prop.user.pk,
                    'username': prop.user.username,
                    'displayName': prop.user.userprofile.get_display_name(),
                    'timestamp': prop.created_on,
                } for prop in properties
            ],
            HTTP_200_OK
        )

    def _validate_list_request(self, request):
        """
        Validates the request parameters.
        Returns a Response object if validation fails, else None.
        """
        requested_user = request.query_params.get('user')
        request_user = request.user
        request_user_is_requested_user_or_superuser = (
                requested_user and
                requested_user.isdigit() and
                request_user.is_authenticated and (
                        requested_user == str(request_user.pk) or
                        request_user.is_superuser
                )
        )

        # Define helper functions for common checks
        def has_param(param):
            return param in request.query_params

        # Validation Rules
        if has_param('has-deepsky-acquisitions') and not requested_user:
            return Response(
                "'user' parameter is required when filtering by deep sky acquisitions.",
                status=HTTP_400_BAD_REQUEST
            )

        if has_param('has-solarsystem-acquisitions') and not requested_user:
            return Response(
                "'user' parameter is required when filtering by solar system acquisitions.",
                status=HTTP_400_BAD_REQUEST
            )

        if has_param('has-deepsky-acquisitions') and has_param('has-solarsystem-acquisitions'):
            return Response(
                "You can only filter by deep sky acquisitions or solar system acquisitions, not both.",
                status=HTTP_400_BAD_REQUEST
            )

        if (has_param('has-deepsky-acquisitions') or has_param(
                'has-solarsystem-acquisitions'
        )) and not request_user_is_requested_user_or_superuser:
            return Response(
                "You can only filter by acquisitions for your own images or if you are a superuser.",
                status=HTTP_403_FORBIDDEN
            )

        if has_param('include-staging-area') and not requested_user:
            return Response(
                "'user' parameter is required when including the staging area.",
                status=HTTP_400_BAD_REQUEST
            )

        if has_param('trash') and not request_user_is_requested_user_or_superuser:
            return Response(
                "You can only request the trash for your own images or if you are a superuser.",
                status=HTTP_403_FORBIDDEN
            )

        if has_param('include-staging-area') and not request_user_is_requested_user_or_superuser:
            return Response(
                "You can only include the staging area for your own images or if you are a superuser.",
                status=HTTP_403_FORBIDDEN
            )

        if has_param('only-staging-area') and not requested_user:
            return Response(
                "'user' parameter is required when requesting the staging area.",
                status=HTTP_400_BAD_REQUEST
            )

        if has_param('only-staging-area') and not request_user_is_requested_user_or_superuser:
            return Response(
                "You can only request the staging area for your own images or if you are a superuser.",
                status=HTTP_403_FORBIDDEN
            )

        # If all validations pass, return None
        return None

    def _get_sorted_queryset_and_extra_data(self, request):
        """
        Sorts the queryset and retrieves 'menu' and 'active' data.
        Returns a tuple of (sorted_queryset, menu, active).
        """
        user = self._get_user(request)
        if not user:
            return self.get_queryset(), None, None

        is_owner = request.user == user
        only_wip = request.query_params.get('only-staging-area')
        include_wip = request.query_params.get('include-staging-area')
        trash = request.query_params.get('trash')
        collection = request.query_params.get('collection')
        subsection = request.query_params.get('subsection', 'uploaded')
        active = request.query_params.get('active')
        q = request.query_params.get('q')
        use_union = subsection in ['uploaded', 'title'] and q is None and collection is None

        if is_owner and only_wip:
            queryset = UserService(user).get_wip_images(use_union=use_union)
        elif is_owner and trash:
            queryset = UserService(user).get_deleted_images()
        elif is_owner and include_wip:
            queryset = UserService(user).get_all_images(use_union=use_union)
        else:
            queryset = UserService(user).get_public_images(use_union=use_union)
        sorted_queryset, menu, active = UserService(user).sort_gallery_by(queryset, subsection, active)
        return sorted_queryset, menu, active

    def _get_user(self, request) -> User:
        if not self.user:
            user_id = request.query_params.get('user')
            self.user = get_object_or_None(User, pk=user_id)
        return self.user
