import re

import simplejson
from django.contrib.postgres.search import TrigramDistance
from django.db.models import Q, QuerySet
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from astrobin_apps_equipment.api.filters.camera_filter import CameraFilter
from astrobin_apps_equipment.api.serializers.camera_image_serializer import CameraImageSerializer
from astrobin_apps_equipment.api.serializers.camera_serializer import CameraSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet
from astrobin_apps_equipment.models import Camera
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_equipment.services.camera_service import CameraService


class CameraViewSet(EquipmentItemViewSet):
    serializer_class = CameraSerializer
    filter_class = CameraFilter

    def get_queryset(self) -> QuerySet:
        include_variants = bool(re.search(r'/equipment/camera/\d+/', self.request.path))
        queryset = super().get_queryset()

        if not include_variants:
            queryset = queryset.filter(CameraService.variant_exclusion_query())

        camera_type_filter = self.request.GET.get('camera-type')
        if camera_type_filter and camera_type_filter != 'null':
            queryset = queryset.filter(type=camera_type_filter)

        camera_cooled_filter = self.request.GET.get('camera-cooled')
        if camera_cooled_filter:
            queryset = queryset.filter(cooled=camera_cooled_filter == 'true')

        camera_max_cooling_filter = self.request.GET.get('camera-max-cooling')
        if camera_max_cooling_filter:
            max_cooling_object = simplejson.loads(camera_max_cooling_filter)
            queryset = queryset.filter(
                max_cooling__isnull=False,
                max_cooling__gte=max_cooling_object.get('from'),
                max_cooling__lte=max_cooling_object.get('to')
            )

        camera_back_focus_filter = self.request.GET.get('camera-back-focus')
        if camera_back_focus_filter:
            back_focus_object = simplejson.loads(camera_back_focus_filter)
            queryset = queryset.filter(
                back_focus__isnull=False,
                back_focus__gte=back_focus_object.get('from'),
                back_focus__lte=back_focus_object.get('to')
            )

        camera_sensor_quantum_efficiency_filter = self.request.GET.get('camera-sensor-quantum-efficiency')
        if camera_sensor_quantum_efficiency_filter:
            sensor_quantum_efficiency_object = simplejson.loads(camera_sensor_quantum_efficiency_filter)
            queryset = queryset.filter(
                sensor__quantum_efficiency__isnull=False,
                sensor__quantum_efficiency__gte=sensor_quantum_efficiency_object.get('from'),
                sensor__quantum_efficiency__lte=sensor_quantum_efficiency_object.get('to')
            )

        camera_sensor_pixel_size_filter = self.request.GET.get('camera-sensor-pixel-size')
        if camera_sensor_pixel_size_filter:
            sensor_pixel_size_object = simplejson.loads(camera_sensor_pixel_size_filter)
            queryset = queryset.filter(
                sensor__pixel_size__isnull=False,
                sensor__pixel_size__gte=sensor_pixel_size_object.get('from'),
                sensor__pixel_size__lte=sensor_pixel_size_object.get('to')
            )

        camera_sensor_pixel_width_filter = self.request.GET.get('camera-sensor-pixel-width')
        if camera_sensor_pixel_width_filter:
            sensor_pixel_width_object = simplejson.loads(camera_sensor_pixel_width_filter)
            queryset = queryset.filter(
                sensor__pixel_width__isnull=False,
                sensor__pixel_width__gte=sensor_pixel_width_object.get('from'),
                sensor__pixel_width__lte=sensor_pixel_width_object.get('to')
            )

        camera_sensor_pixel_height_filter = self.request.GET.get('camera-sensor-pixel-height')
        if camera_sensor_pixel_height_filter:
            sensor_pixel_height_object = simplejson.loads(camera_sensor_pixel_height_filter)
            queryset = queryset.filter(
                sensor__pixel_height__isnull=False,
                sensor__pixel_height__gte=sensor_pixel_height_object.get('from'),
                sensor__pixel_height__lte=sensor_pixel_height_object.get('to')
            )
            
        camera_sensor_width_filter = self.request.GET.get('camera-sensor-width')
        if camera_sensor_width_filter:
            sensor_width_object = simplejson.loads(camera_sensor_width_filter)
            queryset = queryset.filter(
                sensor__sensor_width__isnull=False,
                sensor__sensor_width__gte=sensor_width_object.get('from'),
                sensor__sensor_width__lte=sensor_width_object.get('to')
            )

        camera_sensor_height_filter = self.request.GET.get('camera-sensor-height')
        if camera_sensor_height_filter:
            sensor_height_object = simplejson.loads(camera_sensor_height_filter)
            queryset = queryset.filter(
                sensor__sensor_height__isnull=False,
                sensor__sensor_height__gte=sensor_height_object.get('from'),
                sensor__sensor_height__lte=sensor_height_object.get('to')
            )

        camera_sensor_full_well_capacity_filter = self.request.GET.get('camera-sensor-full-well-capacity')
        if camera_sensor_full_well_capacity_filter:
            full_well_capacity_object = simplejson.loads(camera_sensor_full_well_capacity_filter)
            queryset = queryset.filter(
                sensor__full_well_capacity__isnull=False,
                sensor__full_well_capacity__gte=full_well_capacity_object.get('from'),
                sensor__full_well_capacity__lte=full_well_capacity_object.get('to')
            )

        camera_sensor_read_noise_filter = self.request.GET.get('camera-sensor-read-noise')
        if camera_sensor_read_noise_filter:
            read_noise_object = simplejson.loads(camera_sensor_read_noise_filter)
            queryset = queryset.filter(
                sensor__read_noise__isnull=False,
                sensor__read_noise__gte=read_noise_object.get('from'),
                sensor__read_noise__lte=read_noise_object.get('to')
            )

        camera_sensor_frame_rate_filter = self.request.GET.get('camera-sensor-frame-rate')
        if camera_sensor_frame_rate_filter:
            frame_rate_object = simplejson.loads(camera_sensor_frame_rate_filter)
            queryset = queryset.filter(
                sensor__frame_rate__isnull=False,
                sensor__frame_rate__gte=frame_rate_object.get('from'),
                sensor__frame_rate__lte=frame_rate_object.get('to')
            )

        camera_sensor_adc_filter = self.request.GET.get('camera-sensor-adc')
        if camera_sensor_adc_filter:
            adc_object = simplejson.loads(camera_sensor_adc_filter)
            queryset = queryset.filter(
                sensor__adc__isnull=False,
                sensor__adc__gte=adc_object.get('from'),
                sensor__adc__lte=adc_object.get('to')
            )

        camera_sensor_color_or_mono_filter = self.request.GET.get('camera-sensor-color-or-mono')
        if camera_sensor_color_or_mono_filter and camera_sensor_color_or_mono_filter != 'null':
            queryset = queryset.filter(
                sensor__color_or_mono=camera_sensor_color_or_mono_filter,
            )

        return queryset

    @action(
        detail=True,
        methods=['post'],
        serializer_class=CameraImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(CameraViewSet, self).image_upload(request, pk)

    @action(
        detail=True,
        methods=['get'],
    )
    def variants(self, request, pk):
        base: Camera = get_object_or_404(Camera, pk=pk)

        if base.type != CameraType.DSLR_MIRRORLESS:
            raise ParseError("Only cameras with type DSLR_MIRRORLESS support variants.")

        queryset = Camera.objects.filter(brand=base.brand, name=base.name).exclude(pk=pk).order_by('-modified', '-cooled')
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['GET'],
        url_path='find-similar-in-brand',
    )
    def find_similar_in_brand(self, request):
        brand = request.GET.get('brand')
        q = request.GET.get('q')

        manager = self.get_serializer().Meta.model.objects
        objects = manager.none()

        if brand and q:
            objects = \
                manager.annotate(distance=TrigramDistance('name', q)).filter(
                    Q(brand=int(brand)) &
                    Q(Q(distance__lte=.7) | Q(name__icontains=q)) &
                    ~Q(name=q) &
                    CameraService.variant_exclusion_query()
                ).order_by('distance')[:10]

        serializer = self.serializer_class(objects, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['GET'],
        url_path='others-in-brand',
    )
    def others_in_brand(self, request):
        brand = request.GET.get('brand')

        manager = self.get_serializer().Meta.model.objects
        objects = manager.none()

        if brand:
            objects = manager.filter(Q(brand=int(brand)) & CameraService.variant_exclusion_query()).order_by('name')

        serializer = self.serializer_class(objects, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def approve(self, request, pk):
        camera: Camera = self.get_object()
        if camera.modified or (camera.type == CameraType.DSLR_MIRRORLESS and camera.cooled):
            raise ValidationError(
                'Modified and/or cooled variants of DSLR or mirrorless cameras cannot be edited/approved/rejected '
                'directly. Please find the regular version of this camera and perform this action there.'
            )
        return super().approve(request, pk)


    @action(detail=True, methods=['POST'])
    def reject(self, request, pk):
        camera: Camera = self.get_object()
        if camera.modified or (camera.type == CameraType.DSLR_MIRRORLESS and camera.cooled):
            raise ValidationError(
                'Modified and/or cooled variants of DSLR or mirrorless cameras cannot be edited/approved/rejected '
                'directly. Please find the regular version of this camera and perform this action there.'
            )
        return super().reject(request, pk)
