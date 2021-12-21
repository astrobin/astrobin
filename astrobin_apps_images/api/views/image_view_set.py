# -*- coding: utf-8 -*-
from annoying.functions import get_object_or_None
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from astrobin.models import Image
from astrobin_apps_equipment.models import Accessory, Camera, Filter, Mount, Software, Telescope
from astrobin_apps_images.api.filters import ImageFilter
from astrobin_apps_images.api.permissions import IsImageOwnerOrReadOnly
from astrobin_apps_images.api.serializers import ImageSerializer


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

    def update(self, request, *args, **kwargs):
        data = {}
        equipment_classes = (
            ('imaging_telescopes_2', Telescope),
            ('imaging_cameras_2', Camera),
            ('guiding_telescopes_2', Telescope),
            ('guiding_cameras_2', Camera),
            ('mounts_2', Mount),
            ('filters_2', Filter),
            ('accessories_2', Accessory),
            ('software_2', Software),
        )

        for klass in equipment_classes:
            data[klass[0]] = request.data.pop(klass[0])

        response: Response = super().update(request, *args, **kwargs)
        instance = self.get_object()

        for klass in equipment_classes:
            getattr(instance, klass[0]).clear()
            for item in data[klass[0]]:
                obj = get_object_or_None(klass[1], id=item.get('id'))
                if obj:
                    getattr(instance, klass[0]).add(obj)

        return response
