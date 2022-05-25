import re

from django.contrib.postgres.search import TrigramDistance
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from astrobin_apps_equipment.api.filters.camera_filter import CameraFilter
from astrobin_apps_equipment.api.serializers.camera_image_serializer import CameraImageSerializer
from astrobin_apps_equipment.api.serializers.camera_serializer import CameraSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet
from astrobin_apps_equipment.models import Camera
from astrobin_apps_equipment.models.camera_base_model import CameraType


class CameraViewSet(EquipmentItemViewSet):
    serializer_class = CameraSerializer
    filter_class = CameraFilter

    def get_queryset(self):
        include_variants = bool(re.search(r'/equipment/camera/\d+/', self.request.path))
        queryset = super().get_queryset()

        if not include_variants:
            queryset = queryset.exclude(Q(cooled=True) | Q(modified=True))

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
                    Q(
                        Q(
                            Q(type=CameraType.DSLR_MIRRORLESS) & ~Q(modified=True) & ~Q(cooled=True)
                        ) |
                        ~Q(type=CameraType.DSLR_MIRRORLESS)
                    )
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
            objects = manager.filter(
                Q(brand=int(brand)) &
                Q(
                    Q(
                        Q(type=CameraType.DSLR_MIRRORLESS) & ~Q(modified=True) & ~Q(cooled=True)
                    ) |
                    ~Q(type=CameraType.DSLR_MIRRORLESS)
                )
            ).order_by('name')

        serializer = self.serializer_class(objects, many=True)
        return Response(serializer.data)
