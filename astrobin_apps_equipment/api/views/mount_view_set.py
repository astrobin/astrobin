import sys

import simplejson
from django.db.models import QuerySet
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.filters.mount_filter import MountFilter
from astrobin_apps_equipment.api.serializers.mount_image_serializer import MountImageSerializer
from astrobin_apps_equipment.api.serializers.mount_serializer import MountSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class MountViewSet(EquipmentItemViewSet):
    serializer_class = MountSerializer
    filter_class = MountFilter

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        
        mount_type_filter = self.request.GET.get('mount-type')
        if mount_type_filter and mount_type_filter not in ['null', 'undefined']:
            queryset = queryset.filter(
                type=mount_type_filter,
            )

        mount_weight_filter = self.request.GET.get('mount-weight')
        if mount_weight_filter:
            weight_object = simplejson.loads(mount_weight_filter)
            if weight_object.get('from') is not None or weight_object.get('to') is not None:
                queryset = queryset.filter(
                    weight__isnull=False,
                    weight__gte=weight_object.get('from') if weight_object.get('from') is not None else 0,
                    weight__lte=weight_object.get('to') if weight_object.get('to') is not None else sys.maxsize
                )

        mount_max_payload_filter = self.request.GET.get('mount-max-payload')
        if mount_max_payload_filter:
            max_payload_object = simplejson.loads(mount_max_payload_filter)
            if max_payload_object.get('from') is not None or max_payload_object.get('to') is not None:
                queryset = queryset.filter(
                    max_payload__isnull=False,
                    max_payload__gte=max_payload_object.get('from')
                    if max_payload_object.get('from') is not None
                    else 0,
                    max_payload__lte=max_payload_object.get('to')
                    if max_payload_object.get('to') is not None
                    else sys.maxsize
                )

        mount_computerized_filter = self.request.GET.get('mount-computerized')
        if mount_computerized_filter:
            queryset = queryset.filter(computerized=mount_computerized_filter == 'true')

        mount_periodic_error_filter = self.request.GET.get('mount-periodic-error')
        if mount_periodic_error_filter:
            periodic_error_object = simplejson.loads(mount_periodic_error_filter)
            if periodic_error_object.get('from') is not None or periodic_error_object.get('to') is not None:
                queryset = queryset.filter(
                    periodic_error__isnull=False,
                    periodic_error__gte=periodic_error_object.get('from')
                    if periodic_error_object.get('from') is not None
                    else 0,
                    periodic_error__lte=periodic_error_object.get('to')
                    if periodic_error_object.get('to') is not None
                    else sys.maxsize
                )

        mount_pec_filter = self.request.GET.get('mount-pec')
        if mount_pec_filter:
            queryset = queryset.filter(pec=mount_pec_filter == 'true')

        mount_slew_speed_filter = self.request.GET.get('mount-slew-speed')
        if mount_slew_speed_filter:
            slew_speed_object = simplejson.loads(mount_slew_speed_filter)
            if slew_speed_object.get('from') is not None or slew_speed_object.get('to') is not None:
                queryset = queryset.filter(
                    slew_speed__isnull=False,
                    slew_speed__gte=slew_speed_object.get('from')
                    if slew_speed_object.get('from') is not None
                    else 0,
                    slew_speed__lte=slew_speed_object.get('to')
                    if slew_speed_object.get('to') is not None
                    else sys.maxsize
                )
            
        return queryset
    
    @action(
        detail=True,
        methods=['post'],
        serializer_class=MountImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(MountViewSet, self).image_upload(request, pk)
