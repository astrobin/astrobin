from django.db.models import QuerySet
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.measurement_preset_serializer import MeasurementPresetSerializer
from common.permissions import IsObjectUserOrReadOnly


class MeasurementPresetViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsAuthenticated, IsObjectUserOrReadOnly]
    serializer_class = MeasurementPresetSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet:
        user_id = self.request.query_params.get('user', None)
        if user_id:
            return self.serializer_class.Meta.model.objects.filter(user_id=user_id)

        return self.serializer_class.Meta.model.objects.filter(user=self.request.user)
