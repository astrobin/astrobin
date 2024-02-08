# -*- coding: utf-8 -*-
import logging
from typing import Optional

import simplejson
from annoying.functions import get_object_or_None
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db.models import Count, Value
from django.db.models.functions import Concat
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.viewsets import GenericViewSet

from astrobin.models import DeepSky_Acquisition, Image, SolarSystem_Acquisition
from astrobin_apps_equipment.models import Accessory, Camera, Filter, Mount, Software, Telescope
from astrobin_apps_images.api.filters import ImageFilter
from astrobin_apps_images.api.permissions import IsImageOwnerOrReadOnly
from astrobin_apps_images.api.serializers import ImageSerializer, ImageSerializerSkipThumbnails

logger = logging.getLogger(__name__)


class ImageViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin,
                   GenericViewSet):
    queryset = Image.objects_including_wip.all()
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    filter_class = ImageFilter
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsImageOwnerOrReadOnly
    ]
    http_method_names = ['get', 'head', 'put']
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'images'

    @staticmethod
    def _get_equipment_classes():
        return (
            ('imaging_telescopes_2', Telescope),
            ('imaging_cameras_2', Camera),
            ('guiding_telescopes_2', Telescope),
            ('guiding_cameras_2', Camera),
            ('mounts_2', Mount),
            ('filters_2', Filter),
            ('accessories_2', Accessory),
            ('software_2', Software),
        )

    def _prepare_equipment_data(self, request):
        data = {}

        for klass in ImageViewSet._get_equipment_classes():
            try:
                data[klass[0]] = request.data.pop(klass[0])
            except KeyError:
                data[klass[0]] = []

        return data

    def _update_equipment(self, data, instance: Image):
        for klass in ImageViewSet._get_equipment_classes():
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
                m2m_relation.add(obj)
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
            except Exception as e:
                data_str = simplejson.dumps(data, default=str)
                logger.error(f"Error creating DeepSky_Acquisition: {e}. Data: {data_str}")
                raise e

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

        return queryset

    def update(self, request, *args, **kwargs):
        equipment_data = self._prepare_equipment_data(request)

        response: Response = super().update(request, *args, **kwargs)
        instance: Image = self.get_object()

        self._update_equipment(equipment_data, instance)
        self._update_acquisition(request, instance)

        return response

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
