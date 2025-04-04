from django.db.models import QuerySet
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin_apps_equipment.api.serializers.measurement_preset_serializer import MeasurementPresetSerializer
from astrobin_apps_equipment.models import MeasurementPreset
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
        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        # Check if a preset with the same name already exists for this user
        existing_preset = MeasurementPreset.objects.filter(
            user=request.user,
            name__iexact=request.data.get('name', '')
        ).first()
        
        if existing_preset:
            # Update the existing preset
            update_serializer = self.get_serializer(existing_preset, data=request.data, partial=True)
            update_serializer.is_valid(raise_exception=True)
            self.perform_update(update_serializer)
            return Response(update_serializer.data)
        
        # Otherwise, create a new preset
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
