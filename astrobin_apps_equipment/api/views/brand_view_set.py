import simplejson
from django.contrib.postgres.search import TrigramDistance
from django.core.cache import cache
from django.db.models import Q
from django.db.models.functions import Lower
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from haystack.query import SearchQuerySet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from astrobin_apps_equipment.api.filters.equipment_brand_filter import EquipmentBrandFilter
from astrobin_apps_equipment.api.permissions.is_equipment_moderator_or_own_migrator_or_readonly import \
    IsEquipmentModeratorOrOwnMigratorOrReadOnly
from astrobin_apps_equipment.api.serializers.brand_image_serializer import BrandImageSerializer
from astrobin_apps_equipment.api.serializers.brand_serializer import BrandSerializer
from astrobin_apps_equipment.api.throttle import EquipmentCreateThrottle


class BrandViewSet(viewsets.ModelViewSet):
    serializer_class = BrandSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [IsEquipmentModeratorOrOwnMigratorOrReadOnly]
    filter_class = EquipmentBrandFilter
    http_method_names = ['get', 'post', 'head']
    throttle_classes = [EquipmentCreateThrottle]

    def get_queryset(self):
        q = self.request.GET.get('q')
        sort = self.request.GET.get('sort', 'az')

        manager = self.get_serializer().Meta.model.objects
        queryset = manager.all()

        if q:
            queryset =  manager.annotate(
                distance=TrigramDistance('name', q)
            ).filter(Q(distance__lte=.7) | Q(name__icontains=q)).order_by('distance')
        elif sort == 'az':
            queryset = queryset.order_by(Lower('name'))
        elif sort == '-az':
            queryset = queryset.order_by(Lower('name')).reverse()
        elif sort == 'users':
            queryset = queryset.order_by('user_count', Lower('name'))
        elif sort == '-users':
            queryset = queryset.order_by('-user_count', Lower('name'))
        elif sort == 'images':
            queryset = queryset.order_by('image_count', Lower('name'))
        elif sort == '-images':
            queryset = queryset.order_by('-image_count', Lower('name'))
        return queryset

    @action(
        detail=True,
        methods=['POST'],
        serializer_class=BrandImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def logo(self, request, pk):
        obj = self.get_object()
        serializer = self.serializer_class(obj, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, HTTP_400_BAD_REQUEST)
