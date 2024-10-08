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
from django.db.models import Count, Value
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

from astrobin.models import DeepSky_Acquisition, Image, SolarSystem_Acquisition, UserProfile
from astrobin_apps_equipment.models import Filter
from astrobin_apps_images.api.filters import ImageFilter
from astrobin_apps_images.api.permissions import IsImageOwnerOrReadOnly
from astrobin_apps_images.api.serializers import ImageSerializer, ImageSerializerSkipThumbnails
from astrobin_apps_images.api.serializers.image_serializer_gallery import ImageSerializerGallery
from astrobin_apps_images.api.serializers.image_serializer_trash import ImageSerializerTrash
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_iotd.templatetags.astrobin_apps_iotd_tags import humanize_may_not_submit_to_iotd_tp_process_reason
from astrobin_apps_premium.services.premium_service import PremiumService
from common.permissions import IsSuperUser, or_permission

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
        queryset = super().get_queryset()

        has_deepsky_acquisitions_filter = self.request.GET.get('has-deepsky-acquisitions')
        if has_deepsky_acquisitions_filter and has_deepsky_acquisitions_filter.lower() in ['1', 'true', 'yes']:
            queryset = queryset.annotate(num_deepsky_acquisitions=Count('acquisition__deepsky_acquisition')).filter(
                num_deepsky_acquisitions__gt=0
            )

        has_solarsystem_acquisitions_filter = self.request.GET.get('has-solarsystem-acquisitions')
        if has_solarsystem_acquisitions_filter and has_solarsystem_acquisitions_filter.lower() in ['1', 'true', 'yes']:
            queryset = queryset.annotate(
                num_solarsystem_acquisitions=Count('acquisition__solarsystem_acquisition')
            ).filter(
                num_solarsystem_acquisitions__gt=0
            )

        # Having a hash in the request means we want to retrieve a single image by hash. This should work even if the
        # image is in the staging area, so we act like the retrieval method. This makes the ImageFilter 'hash' field
        # redundant, but we keep it for consistency.
        if 'hash' in self.request.query_params:
            return queryset.filter(hash=self.request.query_params.get('hash'))

        if 'pk' in self.kwargs:
            return queryset.filter(pk=self.kwargs['pk'])

        if (
            self.request.query_params.get('trash') and
            self.request.query_params.get('trash').lower() == 'true'
        ):
            return Image.deleted_objects.filter(user=self.request.user)

        if (
                self.request.query_params.get('include-staging-area') and
                self.request.query_params.get('include-staging-area').lower() == 'true'
        ):
            return queryset

        if (
                self.request.query_params.get('only-staging-area') and
                self.request.query_params.get('only-staging-area').lower() == 'true'
        ):
            return queryset.filter(is_wip=True)

        return queryset.filter(is_wip=False)

    def list(self, request, *args, **kwargs):
        # Perform validation checks here before proceeding to get_queryset
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

        # Handle case where 'include-staging-area' is set but 'user' parameter is missing
        if request.query_params.get('include-staging-area') and not requested_user:
            return Response(
                "'user' parameter is required when including the staging area.",
                status=HTTP_400_BAD_REQUEST
            )

        # Handle permission error when requesting the trash for another user
        if request.query_params.get('trash') and not request_user_is_requested_user_or_superuser:
            return Response(
                "You can only request the trash for your own images or if you are a superuser.",
                status=HTTP_403_FORBIDDEN
            )

        # Handle permission error when requesting staging area for another user
        if request.query_params.get('include-staging-area') and not request_user_is_requested_user_or_superuser:
            return Response(
                "You can only include the staging area for your own images or if you are a superuser.",
                status=HTTP_403_FORBIDDEN
            )

        # Handle case where 'only-staging-area' is set but 'user' parameter is missing
        if request.query_params.get('only-staging-area') and not requested_user:
            return Response(
                "'user' parameter is required when reqiestomg the staging area.",
                status=HTTP_400_BAD_REQUEST
            )

        # Handle permission error when requesting staging area for another user
        if request.query_params.get('only-staging-area') and not request_user_is_requested_user_or_superuser:
            return Response(
                "You can only request the staging area for your own images or if you are a superuser.",
                status=HTTP_403_FORBIDDEN
            )

        # Proceed with the default list behavior
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        # Retrieving an image by PK should work even if the image is in the staging area.
        try:
            instance: Image = get_object_or_None(self.queryset, pk=kwargs['pk'])
        except ValueError:
            return Response(status=HTTP_400_BAD_REQUEST, data={'detail': 'Invalid image ID'})

        if not instance:
            return Response(status=HTTP_404_NOT_FOUND)

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
