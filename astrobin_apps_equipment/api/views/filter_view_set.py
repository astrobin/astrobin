import sys

import simplejson
from django.db.models import QuerySet

from astrobin_apps_equipment.api.filters.filter_filter import FilterFilter
from astrobin_apps_equipment.api.serializers.filter_image_serializer import FilterImageSerializer
from astrobin_apps_equipment.api.serializers.filter_serializer import FilterSerializer
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class FilterViewSet(EquipmentItemViewSet):
    serializer_class = FilterSerializer
    filter_class = FilterFilter

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()

        filter_type_filter = self.request.GET.get('filter-type')
        if filter_type_filter and filter_type_filter != 'null':
            queryset = queryset.filter(
                type=filter_type_filter,
            )

        filter_bandwidth_filter = self.request.GET.get('filter-bandwidth')
        if filter_bandwidth_filter:
            bandwidth_object = simplejson.loads(filter_bandwidth_filter)
            if bandwidth_object.get('from') is not None or bandwidth_object.get('to') is not None:
                queryset = queryset.filter(
                    bandwidth__isnull=False,
                    bandwidth__gte=bandwidth_object.get('from') if bandwidth_object.get('from') is not None else 0,
                    bandwidth__lte=bandwidth_object.get('to') if bandwidth_object.get('to') is not None else sys.maxsize
                )

        filter_size_filter = self.request.GET.get('filter-size')
        if filter_size_filter and filter_size_filter != 'null':
            queryset = queryset.filter(
                size=filter_size_filter,
            )
        
        return queryset

    @action(
        detail=True,
        methods=['post'],
        serializer_class=FilterImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(FilterViewSet, self).image_upload(request, pk)
