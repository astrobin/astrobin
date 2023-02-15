# -*- coding: utf-8 -*-
from annoying.functions import get_object_or_None
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from astrobin.models import DeepSky_Acquisition, Image, SolarSystem_Acquisition
from astrobin_apps_equipment.models import Accessory, Camera, Filter, Mount, Software, Telescope
from astrobin_apps_images.api.filters import ImageFilter
from astrobin_apps_images.api.permissions import IsImageOwnerOrReadOnly
from astrobin_apps_images.api.serializers import ImageSerializer
from astrobin_apps_images.api.serializers.deep_sky_acquisition_serializer import DeepSkyAcquisitionSerializer
from astrobin_apps_images.api.serializers.solar_system_acquisition_serializer import SolarSystemAcquisitionSerializer
from astrobin_apps_users.services import UserService
from common.constants import GroupName


class ImageViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin,
                   GenericViewSet):
    serializer_class = ImageSerializer
    queryset = Image.objects_including_wip.all()
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    filter_class = ImageFilter
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsImageOwnerOrReadOnly
    ]
    http_method_names = ['get', 'head', 'put']

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
            getattr(instance, klass[0]).clear()
            for item in data[klass[0]]:
                obj = get_object_or_None(klass[1], id=item if type(item) == int else item.get('id'))
                if obj:
                    getattr(instance, klass[0]).add(obj)

    def _update_acquisition(self, request, instance: Image):
        if not UserService(request.user).is_in_group([GroupName.ACQUISITION_EDIT_TESTERS]):
            return

        DeepSky_Acquisition.objects.filter(image=instance).delete()
        for item in request.data.get('deep_sky_acquisitions'):
            if item.get('filter_2'):
                item['filter_2'] = Filter.objects.get(id=item.get('filter_2'))

            data = dict(image=instance, **item)
            if 'id' in data:
                del data['id']
            DeepSky_Acquisition.objects.create(**data)

        SolarSystem_Acquisition.objects.filter(image=instance).delete()
        for item in request.data.get('solar_system_acquisitions'):
            data = dict(image=instance, **item)
            if 'id' in data:
                del data['id']
            SolarSystem_Acquisition.objects.create(**data)

    def update(self, request, *args, **kwargs):
        equipment_data = self._prepare_equipment_data(request)

        response: Response = super().update(request, *args, **kwargs)
        instance: Image = self.get_object()

        self._update_equipment(equipment_data, instance)
        self._update_acquisition(request, instance)

        return response
