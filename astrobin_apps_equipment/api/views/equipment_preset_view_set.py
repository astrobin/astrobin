from django.db.models import QuerySet
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from astrobin_apps_equipment.api.serializers.equipment_preset_image_serializer import EquipmentPresetImageSerializer
from astrobin_apps_equipment.api.serializers.equipment_preset_serializer import EquipmentPresetSerializer
from common.permissions import IsObjectUserOrReadOnly


class EquipmentPresetViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsAuthenticated, IsObjectUserOrReadOnly]
    serializer_class = EquipmentPresetSerializer
    pagination_class = None

    def get_queryset(self) -> QuerySet:
        user_id = self.request.query_params.get('user', None)
        if user_id:
            return self.serializer_class.Meta.model.objects.filter(user_id=user_id)

        return self.serializer_class.Meta.model.objects.filter(user=self.request.user)

    @action(
        detail=True,
        methods=['post'],
        serializer_class=EquipmentPresetImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk: int) -> Response:
        obj = self.get_object()
        serializer = self.serializer_class(obj, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['post'],
        url_path='clear-image',
    )
    def clear_image(self, request, pk: int) -> Response:
        obj = self.get_object()

        if obj.image_file is not None:
            obj.image_file = None
            obj.save()

        return Response(self.serializer_class(obj).data)
