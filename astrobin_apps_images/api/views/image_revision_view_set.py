# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import mixins
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.viewsets import GenericViewSet

from astrobin.models import ImageRevision
from astrobin_apps_images.api.filters import ImageRevisionFilter
from astrobin_apps_images.api.permissions import IsImageOwnerOrReadOnly
from astrobin_apps_images.api.serializers import ImageRevisionSerializer


class ImageRevisionViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin,
                           mixins.ListModelMixin,
                           GenericViewSet):
    serializer_class = ImageRevisionSerializer
    queryset = ImageRevision.objects.all()
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    filter_class = ImageRevisionFilter
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsImageOwnerOrReadOnly
    ]
    http_method_names = ['get', 'head', 'put']
