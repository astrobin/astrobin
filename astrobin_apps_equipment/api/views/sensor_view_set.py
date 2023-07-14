import sys

import simplejson
from django.db.models import QuerySet
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser

from astrobin_apps_equipment.api.filters.sensor_filter import SensorFilter
from astrobin_apps_equipment.api.serializers.sensor_image_serializer import SensorImageSerializer
from astrobin_apps_equipment.api.serializers.sensor_serializer import SensorSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class SensorViewSet(EquipmentItemViewSet):
    serializer_class = SensorSerializer
    filter_class = SensorFilter

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()

        sensor_quantum_efficiency_filter = self.request.GET.get('sensor-quantum-efficiency')
        if sensor_quantum_efficiency_filter:
            sensor_quantum_efficiency_object = simplejson.loads(sensor_quantum_efficiency_filter)
            if sensor_quantum_efficiency_object.get('from') is not None \
                    or sensor_quantum_efficiency_object.get('to') is not None:
                queryset = queryset.filter(
                    quantum_efficiency__isnull=False,
                    quantum_efficiency__gte=sensor_quantum_efficiency_object.get('from')
                    if sensor_quantum_efficiency_object.get('from')
                    else 0,
                    quantum_efficiency__lte=sensor_quantum_efficiency_object.get('to')
                    if sensor_quantum_efficiency_object.get('to')
                    else sys.maxsize
                )

        sensor_pixel_size_filter = self.request.GET.get('sensor-pixel-size')
        if sensor_pixel_size_filter:
            sensor_pixel_size_object = simplejson.loads(sensor_pixel_size_filter)
            if sensor_pixel_size_object.get('from')  is not None or sensor_pixel_size_object.get('to') is not None:
                queryset = queryset.filter(
                    pixel_size__isnull=False,
                    pixel_size__gte=sensor_pixel_size_object.get('from')
                    if sensor_pixel_size_object.get('from') is not None
                    else 0,
                    pixel_size__lte=sensor_pixel_size_object.get('to')
                    if sensor_pixel_size_object.get('to') is not None
                    else sys.maxsize
                )

        sensor_pixel_width_filter = self.request.GET.get('sensor-pixel-width')
        if sensor_pixel_width_filter:
            sensor_pixel_width_object = simplejson.loads(sensor_pixel_width_filter)
            if sensor_pixel_width_filter.get('from') is not None or sensor_pixel_width_filter.get('to') is not None:
                queryset = queryset.filter(
                    pixel_width__isnull=False,
                    pixel_width__gte=sensor_pixel_width_object.get('from')
                    if sensor_pixel_width_object.get('from') is not None else 0,
                    pixel_width__lte=sensor_pixel_width_object.get('to')
                    if sensor_pixel_width_object.get('to') is not None
                    else sys.maxsize
                )

        sensor_pixel_height_filter = self.request.GET.get('sensor-pixel-height')
        if sensor_pixel_height_filter:
            sensor_pixel_height_object = simplejson.loads(sensor_pixel_height_filter)
            if sensor_pixel_height_object.get('from') is not None or sensor_pixel_height_object.get('to') is not None:
                queryset = queryset.filter(
                    pixel_height__isnull=False,
                    pixel_height__gte=sensor_pixel_height_object.get('from')
                    if sensor_pixel_height_object.get('from') is not None
                    else 0,
                    pixel_height__lte=sensor_pixel_height_object.get('to')
                    if sensor_pixel_height_object.get('to')
                    else sys.maxsize
                )

        sensor_width_filter = self.request.GET.get('sensor-width')
        if sensor_width_filter:
            sensor_width_object = simplejson.loads(sensor_width_filter)
            if sensor_width_object.get('from') is not None or sensor_width_object.get('to') is not None:
                queryset = queryset.filter(
                    sensor_width__isnull=False,
                    sensor_width__gte=sensor_width_object.get('from')
                    if sensor_width_object.get('from') is not None
                    else 0,
                    sensor_width__lte=sensor_width_object.get('to')
                    if sensor_width_object.get('to') is not None
                    else sys.maxsize
                )

        sensor_height_filter = self.request.GET.get('sensor-height')
        if sensor_height_filter:
            sensor_height_object = simplejson.loads(sensor_height_filter)
            if sensor_height_object.get('from') is not None or sensor_height_object.get('to') is not None:
                queryset = queryset.filter(
                    sensor_height__isnull=False,
                    sensor_height__gte=sensor_height_object.get('from')
                    if sensor_height_object.get('from') is not None
                    else 0,
                    sensor_height__lte=sensor_height_object.get('to')
                    if sensor_height_object.get('to') is not None
                    else sys.maxsize
                )

        sensor_full_well_capacity_filter = self.request.GET.get('sensor-full-well-capacity')
        if sensor_full_well_capacity_filter:
            full_well_capacity_object = simplejson.loads(sensor_full_well_capacity_filter)
            if full_well_capacity_object.get('from') is not None or full_well_capacity_object.get('to') is not None:
                queryset = queryset.filter(
                    full_well_capacity__isnull=False,
                    full_well_capacity__gte=full_well_capacity_object.get('from')
                    if full_well_capacity_object.get('from') is not None
                    else 0,
                    full_well_capacity__lte=full_well_capacity_object.get('to')
                    if full_well_capacity_object.get('to') is not None
                    else sys.maxsize
                )

        sensor_read_noise_filter = self.request.GET.get('sensor-read-noise')
        if sensor_read_noise_filter:
            read_noise_object = simplejson.loads(sensor_read_noise_filter)
            if read_noise_object.get('from') is not None or read_noise_object.get('from') is not None:
                queryset = queryset.filter(
                    read_noise__isnull=False,
                    read_noise__gte=read_noise_object.get('from')
                    if read_noise_object.get('from') is not None
                    else 0,
                    read_noise__lte=read_noise_object.get('to')
                    if read_noise_object.get('to') is not None
                    else sys.maxsize
                )

        sensor_frame_rate_filter = self.request.GET.get('sensor-frame-rate')
        if sensor_frame_rate_filter:
            frame_rate_object = simplejson.loads(sensor_frame_rate_filter)
            if frame_rate_object.get('from') is not None or frame_rate_object.get('to') is not None:
                queryset = queryset.filter(
                    frame_rate__isnull=False,
                    frame_rate__gte=frame_rate_object.get('from')
                    if frame_rate_object.get('from') is not None
                    else 0,
                    frame_rate__lte=frame_rate_object.get('to')
                    if frame_rate_object.get('to') is not None
                    else sys.maxsize
                )

        sensor_adc_filter = self.request.GET.get('sensor-adc')
        if sensor_adc_filter:
            adc_object = simplejson.loads(sensor_adc_filter)
            if adc_object.get('from') is not None or adc_object.get('to') is not None:
                queryset = queryset.filter(
                    adc__isnull=False,
                    adc__gte=adc_object.get('from') if adc_object.get('from') is not None else 0,
                    adc__lte=adc_object.get('to') if adc_object.get('to') is not None else sys.maxsize
                )

        sensor_color_or_mono_filter = self.request.GET.get('sensor-color-or-mono')
        if sensor_color_or_mono_filter and sensor_color_or_mono_filter not in ['null', 'undefined']:
            queryset = queryset.filter(
                color_or_mono=sensor_color_or_mono_filter,
            )

        return queryset

    @action(
        detail=True,
        methods=['POST'],
        serializer_class=SensorImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(SensorViewSet, self).image_upload(request, pk)
