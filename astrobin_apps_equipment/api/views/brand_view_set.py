from django.contrib.postgres.search import TrigramDistance
from django.db.models import Count, Q
from django.db.models.functions import Lower
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from astrobin.api2.throttle import MultiRateThrottle
from astrobin.utils import get_client_country_code
from astrobin_apps_equipment.api.filters.equipment_brand_filter import EquipmentBrandFilter
from astrobin_apps_equipment.api.permissions.is_equipment_moderator_or_own_migrator_or_readonly import \
    IsEquipmentModeratorOrOwnMigratorOrReadOnly
from astrobin_apps_equipment.api.serializers.brand_image_serializer import BrandImageSerializer
from astrobin_apps_equipment.api.serializers.brand_listing_serializer import BrandListingSerializer
from astrobin_apps_equipment.api.serializers.brand_serializer import BrandSerializer
from astrobin_apps_equipment.api.throttle import EquipmentCreateThrottle
from astrobin_apps_equipment.models import EquipmentBrand
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.services import EquipmentService
from astrobin_apps_premium.services.premium_service import PremiumService


class BrandViewSet(viewsets.ModelViewSet):
    serializer_class = BrandSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [IsEquipmentModeratorOrOwnMigratorOrReadOnly]
    filter_class = EquipmentBrandFilter
    http_method_names = ['get', 'post', 'head']
    throttle_classes = [EquipmentCreateThrottle, MultiRateThrottle]

    def get_queryset(self):
        q = self.request.GET.get('q')
        sort = self.request.GET.get('sort', 'az')
        type_ = self.request.GET.get('type')

        manager = self.get_serializer().Meta.model.objects
        queryset = manager.all()

        if type_ and type_.upper() not in [i for i in EquipmentItemKlass.__dict__.keys() if i[:1] != '_']:
            return manager.none()

        if q:
            queryset =  manager.annotate(
                distance=TrigramDistance('name', q)
            ).filter(Q(distance__lte=.7) | Q(name__icontains=q)).order_by('distance')
        elif type_:
            queryset = manager.annotate(
                count=Count(f'astrobin_apps_equipment_brand_{type_}s')
            ).filter(
                count__gt=0
            ).order_by(
                Lower('name')
            )
            self.paginator.page_size = queryset.count()
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

    @action(detail=True, methods=['GET'])
    def listings(self, request, pk: int) -> Response:
        brand: EquipmentBrand = self.get_object()

        valid_user_subscription = PremiumService(request.user).get_valid_usersubscription()
        allow_full_retailer_integration = PremiumService.allow_full_retailer_integration(valid_user_subscription, None)

        brand_listings = EquipmentService.equipment_brand_listings_by_brand(brand, get_client_country_code(request))

        return Response(
            dict(
                brand_listings=BrandListingSerializer(brand_listings, many=True).data,
                item_listings=[],
                allow_full_retailer_integration=allow_full_retailer_integration,
            )
        )

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
