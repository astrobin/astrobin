from django.contrib.postgres.search import TrigramDistance
from django.db.models import Q
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.filters.equipment_brand_filter import EquipmentBrandFilter
from astrobin_apps_equipment.api.permissions.is_equipment_moderator_or_read_only import IsEquipmentModeratorOrReadOnly
from astrobin_apps_equipment.api.serializers.brand_serializer import BrandSerializer


class BrandViewSet(viewsets.ModelViewSet):
    serializer_class = BrandSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [IsEquipmentModeratorOrReadOnly]
    filter_class = EquipmentBrandFilter
    http_method_names = ['get', 'post', 'head', 'put', 'patch']

    def get_queryset(self):
        q = self.request.GET.get('q')
        manager = self.get_serializer().Meta.model.objects

        if not q:
            return manager.all()

        return manager.annotate(
            distance=TrigramDistance('name', q)
        ).filter(Q(distance__lte=.7) | Q(name__icontains=q)).order_by('distance')