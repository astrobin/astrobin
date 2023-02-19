from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.api2.serializers.deepsky_acquisition_preset_serializer import DeepSkyAcquisitionPresetSerializer
from common.permissions import IsObjectUserOrReadOnly


class DeepSkyAcquisitionPresetViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsObjectUserOrReadOnly]
    serializer_class = DeepSkyAcquisitionPresetSerializer
    pagination_class = None

    def get_queryset(self):
        return self.serializer_class.Meta.model.objects.filter(user=self.request.user)
