# -*- coding: utf-8 -*-
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.models import DeepSky_Acquisition
from astrobin_apps_images.api.permissions import IsImageOwnerOrReadOnly
from astrobin_apps_images.api.serializers.deep_sky_acquisition_serializer import DeepSkyAcquisitionSerializer


class DeepSkyAcquisitionViewSet(viewsets.ModelViewSet):
    serializer_class = DeepSkyAcquisitionSerializer
    queryset = DeepSky_Acquisition.objects.all()
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsImageOwnerOrReadOnly
    ]
    http_method_names = ['get', 'head', 'put', 'post']
