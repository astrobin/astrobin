from django.contrib.postgres.search import TrigramDistance
from django.db.models import Count, Q
from django.db.models.functions import Lower
from django.utils.translation import gettext
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from astrobin.utils import get_client_country_code
from astrobin_apps_equipment.api.filters.equipment_brand_filter import EquipmentBrandFilter
from astrobin_apps_equipment.api.permissions.is_equipment_moderator_or_own_migrator_or_readonly import \
    IsEquipmentModeratorOrOwnMigratorOrReadOnly
from astrobin_apps_equipment.api.serializers.brand_image_serializer import BrandImageSerializer
from astrobin_apps_equipment.api.serializers.brand_listing_serializer import BrandListingSerializer
from astrobin_apps_equipment.api.serializers.brand_serializer import BrandSerializer
from astrobin_apps_equipment.api.throttle import EquipmentCreateThrottle
from astrobin_apps_equipment.models import EquipmentBrand
from astrobin_apps_equipment.models.equipment_item import EquipmentItemReviewerDecision
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass
from astrobin_apps_equipment.services import EquipmentService
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_users.services import UserService
from common.constants import GroupName


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
        type_ = self.request.GET.get('type')

        manager = self.get_serializer().Meta.model.objects
        queryset = manager

        equipment_types = [k.lower() for k in vars(EquipmentItemKlass) if not k.startswith("__")]

        # We only want the brands that have at least one approved item, if the user is not a moderator
        # ==============================================================================================================

        if not UserService(self.request.user).is_in_group(GroupName.EQUIPMENT_MODERATORS):
            # Loop over the equipment types and add an annotation for each
            for equipment_type in equipment_types:
                queryset = queryset.annotate(
                    **{
                        f'approved_{equipment_type}_count': Count(
                            f'astrobin_apps_equipment_brand_{equipment_type}s',
                            filter=Q(
                                **{
                                    f'astrobin_apps_equipment_brand_{equipment_type}s__reviewer_decision': EquipmentItemReviewerDecision.APPROVED
                                }
                            )
                        )
                    }
                )

            # Build Q objects for the filter
            q_objects = Q(created_by=self.request.user) if self.request.user.is_authenticated else Q()
            for equipment_type in equipment_types:
                q_objects |= Q(**{f'approved_{equipment_type}_count__gt': 0})

            # Apply the filter
            queryset = queryset.filter(q_objects)
        # ==============================================================================================================

        if type_ and type_.lower() not in equipment_types:
            return manager.none()

        if q:
            queryset = queryset.annotate(
                distance=TrigramDistance('name', q)
            ).filter(Q(distance__lte=.7) | Q(name__icontains=q)).order_by('distance')
        elif type_:
            queryset = queryset.annotate(
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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            if 'name' in serializer.errors and serializer.errors['name'][0].code == 'unique':
                return Response({
                    "name": gettext(
                        "This brand already exists, but it might not be approved by a moderator yet. Please try again "
                        "later or contact support if the problem persists."
                    )
                }, status=status.HTTP_400_BAD_REQUEST)

            raise

        return super().create(request, *args, **kwargs)

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
