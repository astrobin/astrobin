from rest_framework import viewsets

from astrobin_apps_equipment.models import Brand, EquipmentItem
from astrobin_apps_equipment.serializers import BrandSerializer, EquipmentItemSerializer


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer


class EquipmentItemViewSet(viewsets.ModelViewSet):
    queryset = EquipmentItem.objects.all()
    serializer_class = EquipmentItemSerializer
