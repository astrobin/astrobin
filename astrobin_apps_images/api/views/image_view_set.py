# -*- coding: utf-8 -*-
from collections import namedtuple

import simplejson
from django.http.response import Http404, HttpResponse
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from hitcount.models import HitCount
from hitcount.views import HitCountMixin
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.viewsets import GenericViewSet

from astrobin.models import Image
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

    @action(detail=True, methods=['put'])
    def hit(self, request, pk):
        UpdateHitCountResponse = namedtuple('UpdateHitCountResponse', 'hit_counted hit_message')

        try:
            image: Image = Image.objects_including_wip.get(pk=pk)
            if request.user != image.user:
                hit_count: HitCount = HitCount.objects.get_for_object(image)
                hit_count_response: UpdateHitCountResponse = HitCountMixin.hit_count(request, hit_count)
                return HttpResponse(simplejson.dumps(hit_count_response))
            else:
                return HttpResponse(simplejson.dumps(UpdateHitCountResponse(False, 'Hit from image owner ignored')))
        except self.serializer_class.Meta.model.DoesNotExist:
            raise Http404
