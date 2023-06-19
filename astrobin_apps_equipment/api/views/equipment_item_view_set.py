import logging
from collections import Counter
from typing import List, Optional

import simplejson
from annoying.functions import get_object_or_None
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import TrigramDistance
from django.core.cache import cache
from django.db.models import IntegerField, Q, QuerySet, Value
from django.db.models.functions import Concat, Lower
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import cache_page
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from haystack.query import SearchQuerySet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT

from astrobin.models import Image
from astrobin.utils import get_client_country_code
from astrobin_apps_equipment.api.permissions.is_equipment_moderator_or_own_migrator_or_readonly import \
    IsEquipmentModeratorOrOwnMigratorOrReadOnly
from astrobin_apps_equipment.api.serializers.brand_listing_serializer import BrandListingSerializer
from astrobin_apps_equipment.api.serializers.item_listing_serializer import ItemListingSerializer
from astrobin_apps_equipment.api.throttle import EquipmentCreateThrottle
from astrobin_apps_equipment.models import EquipmentBrand, EquipmentItem
from astrobin_apps_equipment.models.equipment_item import EquipmentItemReviewerDecision
from astrobin_apps_equipment.services import EquipmentService
from astrobin_apps_equipment.services.equipment_item_service import EquipmentItemService
from astrobin_apps_equipment.tasks import reject_item
from astrobin_apps_notifications.utils import build_notification_url, push_notification
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import can_access_full_search
from astrobin_apps_users.services import UserService
from common.constants import GroupName
from common.services import AppRedirectionService
from toggleproperties.models import ToggleProperty

log = logging.getLogger(__name__)


class EquipmentItemViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsEquipmentModeratorOrOwnMigratorOrReadOnly]
    http_method_names = ['get', 'post', 'head']
    throttle_classes = [EquipmentCreateThrottle]

    def _conflict_response(self):
        return Response(
            data=_('Someone else is working on this item right now. Please try again later.'),
            status=HTTP_409_CONFLICT
        )

    def get_queryset(self) -> QuerySet:
        q = self.request.query_params.get('q')
        sort = self.request.query_params.get('sort')
        brand_from_query = self.request.query_params.get('brand')

        manager = self.get_serializer().Meta.model.objects
        queryset = manager.all()

        if 'include-variants' in self.request.query_params and self.request.query_params.get(
                'include-variants'
        ).lower() == 'false':
            queryset = queryset.filter(variant_of__isnull=True)

        if 'EditProposal' not in str(self.get_serializer().Meta.model):
            if self.request.user.is_authenticated:
                if not UserService(self.request.user).is_in_group(GroupName.EQUIPMENT_MODERATORS):
                    queryset = queryset.filter(EquipmentItemService.non_moderator_queryset(self.request.user))
            else:
                queryset = queryset.filter(
                    brand__isnull=False,
                    reviewer_decision=EquipmentItemReviewerDecision.APPROVED,
                )

        if q:
            brand = get_object_or_None(EquipmentBrand, name__iexact=q)
            brand_queryset: QuerySet = queryset.none()
            if brand:
                query = Q(brand=brand)
                if not UserService(self.request.user).is_in_group(GroupName.EQUIPMENT_MODERATORS):
                    query &= Q(
                        Q(reviewer_decision=EquipmentItemReviewerDecision.APPROVED) |
                        (Q(created_by=self.request.user) if self.request.user.is_authenticated else Q(pk=None))
                    )
                brand_queryset = queryset.filter(query).order_by(Lower('name'))
            if brand_queryset.exists():
                self.paginator.page_size = brand_queryset.count()
                queryset = brand_queryset
            else:
                if 'postgresql' in settings.DATABASES['default']['ENGINE']:
                    contains_queryset = queryset.annotate(
                        full_name=Concat('brand__name', Value(' '), 'name'),
                        search_friendly_distance=TrigramDistance('search_friendly_name', q),
                        full_name_distance=TrigramDistance('full_name', q),
                        custom_order=Value(1, IntegerField()),
                    ).filter(
                        Q(
                            Q(search_friendly_name__icontains=q) |
                            Q(variants__search_friendly_name__icontains=q) |
                            Q(full_name__icontains=q) |
                            Q(variants__name__icontains=q)
                        )
                    ).distinct()

                    distance_queryset = queryset.annotate(
                        full_name=Concat('brand__name', Value(' '), 'name'),
                        search_friendly_distance=TrigramDistance('search_friendly_name', q),
                        full_name_distance=TrigramDistance('full_name', q),
                        custom_order=Value(2, IntegerField()),
                    ).filter(
                        Q(
                            Q(search_friendly_distance__lte=.85) |
                            Q(full_name_distance__lte=.85)
                        ) &
                        ~Q(pk__in=contains_queryset.values_list('pk', flat=True))
                    ).distinct()

                    queryset = contains_queryset.union(distance_queryset).order_by(
                        'custom_order',
                        'search_friendly_distance',
                        'full_name_distance',
                    )
                else:
                    queryset = queryset.annotate(
                        full_name=Concat('brand__name', Value(' '), 'name')
                    ).filter(
                        Q(
                            Q(search_friendly_name__icontains=q) |
                            Q(variants__search_friendly_name__icontains=q) |
                            Q(full_name__icontains=q) |
                            Q(variants__name__icontains=q)
                        )
                    ).distinct(
                    ).order_by(
                        Lower('search_friendly_name'),
                        Lower('full_name'),
                    )

                queryset = queryset[:50]
        elif sort == 'az':
            queryset = queryset.order_by(Lower('search_friendly_name'))
        elif sort == '-az':
            queryset = queryset.order_by(Lower('search_friendly_name')).reverse()
        elif sort == 'users':
            queryset = queryset.order_by('user_count', Lower('search_friendly_name'))
        elif sort == '-users':
            queryset = queryset.order_by('-user_count', Lower('search_friendly_name'))
        elif sort == 'images':
            queryset = queryset.order_by('image_count', Lower('search_friendly_name'))
        elif sort == '-images':
            queryset = queryset.order_by('-image_count', Lower('search_friendly_name'))

        if brand_from_query is not None:
            queryset = queryset.filter(brand=brand_from_query)

        return queryset

    @method_decorator(cache_page(60*60))
    @action(detail=False, methods=['get'])
    def count(self, request):
        return Response(self.get_queryset().count())

    @action(
        detail=True,
        methods=['get'],
    )
    def variants(self, request, pk):
        manager = self.get_serializer().Meta.model.objects
        item: EquipmentItem = get_object_or_404(manager, pk=pk)

        if self.request.user.is_authenticated:
            if not UserService(self.request.user).is_in_group(GroupName.EQUIPMENT_MODERATORS):
                queryset = item.variants.filter(EquipmentItemService.non_moderator_queryset(request.user))
            else:
                queryset = item.variants.all()
        else:
            queryset = item.variants.filter(
                brand__isnull=False,
                reviewer_decision=EquipmentItemReviewerDecision.APPROVED,
            )

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['GET'],
        url_path='recently-used'
    )
    def find_recently_used(self, request):
        manager = self.get_serializer().Meta.model.objects
        objects = manager.none()

        from astrobin_apps_equipment.models import Sensor
        from astrobin_apps_equipment.models import Camera
        from astrobin_apps_equipment.models import Telescope
        from astrobin_apps_equipment.models import Mount
        from astrobin_apps_equipment.models import Filter
        from astrobin_apps_equipment.models import Accessory
        from astrobin_apps_equipment.models import Software

        if manager.model == Sensor:
            return Response("This API does not support sensors", HTTP_400_BAD_REQUEST)

        if request.user.is_authenticated:
            usage_type = request.query_params.get('usage-type')
            recent_items = []
            images: QuerySet[Image] = Image.objects_including_wip.filter(user=request.user).order_by('-uploaded')

            image: Image
            for image in images.iterator():
                if len(recent_items) > 10:
                    break

                prop: str = Optional[None]
                if manager.model == Camera:
                    if usage_type == 'imaging':
                        prop = 'imaging_cameras_2'
                    elif usage_type == 'guiding':
                        prop = 'guiding_cameras_2'
                    else:
                        return Response("You need to specify a 'usage_type' with cameras", HTTP_400_BAD_REQUEST)
                elif manager.model == Telescope:
                    if usage_type == 'imaging':
                        prop = 'imaging_telescopes_2'
                    elif usage_type == 'guiding':
                        prop = 'guiding_telescopes_2'
                    else:
                        return Response("You need to specify a 'usage_type' with telescopes", HTTP_400_BAD_REQUEST)
                elif manager.model == Mount:
                    prop = 'mounts_2'
                elif manager.model == Filter:
                    prop = 'filters_2'
                elif manager.model == Accessory:
                    prop = 'accessories_2'
                elif manager.model == Software:
                    prop = 'software_2'

                if prop:
                    x: EquipmentItem
                    for x in getattr(image, prop).all():
                        if not x.frozen_as_ambiguous and x.pk not in recent_items:
                            recent_items.append(x.pk)

            objects = manager.filter(pk__in=recent_items)

        serializer = self.serializer_class(objects, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['GET'],
        url_path='followed'
    )
    def find_followed(self, request):
        manager = self.get_serializer().Meta.model.objects

        if not request.user.is_authenticated:
            return Response(self.serializer_class(manager.none(), many=True).data)

        object_ids: List[str] = ToggleProperty.objects.filter(
            user=request.user,
            content_type=ContentType.objects.get_for_model(manager.model),
            property_type='follow',
        ).values_list('object_id', flat=True)

        serializer = self.serializer_class(
            manager.filter(pk__in=[int(x) for x in object_ids]),
            many=True,
            context={'request': request}
        )
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
        queryset = manager.none()

        if brand and q:
            queryset = manager.annotate(
                distance=TrigramDistance('name', q)
            ).filter(
                Q(brand=int(brand)) &
                Q(Q(distance__lte=.7) | Q(name__icontains=q)) &
                ~Q(name=q)
            )

            if not request.user.is_authenticated or not UserService(request.user).is_in_group(
                    GroupName.EQUIPMENT_MODERATORS
            ):
                queryset = queryset.filter(EquipmentItemService.non_moderator_queryset(request.user))

            queryset = queryset.order_by(
                'distance'
            )[:10]

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['GET'],
        url_path='others-in-brand',
    )
    def others_in_brand(self, request):
        brand = request.query_params.get('brand')
        name = request.query_params.get('name')

        manager = self.get_serializer().Meta.model.objects
        queryset = manager.none()

        if brand:
            queryset = manager.filter(brand=int(brand)).order_by('name')
            if name:
                queryset = queryset.exclude(name__iexact=name)

            if not request.user.is_authenticated or not UserService(request.user).is_in_group(
                    GroupName.EQUIPMENT_MODERATORS
            ):
                queryset = queryset.filter(EquipmentItemService.non_moderator_queryset(request.user))

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'], url_path='acquire-reviewer-lock')
    def acquire_reviewer_lock(self, request, pk):
        if not UserService(request.user).is_in_group(GroupName.EQUIPMENT_MODERATORS):
            raise PermissionDenied(request.user)

        item: EquipmentItem = self.get_object()

        if item.reviewer_lock and item.reviewer_lock != request.user:
            return self._conflict_response()

        item.reviewer_lock = request.user
        item.reviewer_lock_timestamp = timezone.now()
        item.save(keep_deleted=True)

        return Response(status=HTTP_200_OK)

    @action(detail=True, methods=['POST'], url_path='release-reviewer-lock')
    def release_reviewer_lock(self, request, pk):
        item: EquipmentItem = self.get_object()

        if item.reviewer_lock == request.user:
            item.reviewer_lock = None
            item.reviewer_lock_timestamp = None
            item.save(keep_deleted=True)

        return Response(status=HTTP_200_OK)

    @action(detail=True, methods=['POST'], url_path='acquire-edit-proposal-lock')
    def acquire_edit_proposal_lock(self, request, pk):
        if not UserService(request.user).is_in_group(GroupName.OWN_EQUIPMENT_MIGRATORS):
            raise PermissionDenied(request.user)

        item: EquipmentItem = self.get_object()

        if item.edit_proposal_lock and item.edit_proposal_lock != request.user:
            return self._conflict_response()

        item.edit_proposal_lock = request.user
        item.edit_proposal_lock_timestamp = timezone.now()
        item.save(keep_deleted=True)

        return Response(status=HTTP_200_OK)

    @action(detail=True, methods=['POST'], url_path='release-edit-proposal-lock')
    def release_edit_proposal_lock(self, request, pk):
        item: EquipmentItem = self.get_object()

        if item.edit_proposal_lock == request.user:
            item.edit_proposal_lock = None
            item.edit_proposal_lock_timestamp = None
            item.save(keep_deleted=True)

        return Response(status=HTTP_200_OK)

    @action(detail=True, methods=['GET'], url_path='possible-assignees')
    def possible_assignees(self, request, pk):
        if not UserService(request.user).is_in_group(GroupName.EQUIPMENT_MODERATORS):
            raise PermissionDenied(request.user)

        item: EquipmentItem = get_object_or_404(self.get_serializer().Meta.model.objects, pk=pk)
        value = []

        for moderator in User.objects.filter(groups__name=GroupName.EQUIPMENT_MODERATORS):
            if moderator != item.created_by and moderator.pk not in [x.get('key') for x in value]:
                value.append(dict(
                    key=moderator.pk,
                    value=moderator.userprofile.get_display_name(),
                ))

        return Response(status=200, data=value)

    @action(detail=True, methods=['POST'])
    def assign(self, request, pk):
        if not UserService(request.user).is_in_group(GroupName.EQUIPMENT_MODERATORS):
            raise PermissionDenied(request.user)

        item: EquipmentItem = get_object_or_404(self.get_serializer().Meta.model.objects, pk=pk)
        new_assignee_pk = request.data.get('assignee')
        new_assignee = None

        if new_assignee_pk:
            new_assignee = get_object_or_None(User, pk=new_assignee_pk)
            if new_assignee is None:
                return Response("User not found", HTTP_400_BAD_REQUEST)

            if not UserService(new_assignee).is_in_group(GroupName.EQUIPMENT_MODERATORS):
                return Response("Assignee is not a moderator", HTTP_400_BAD_REQUEST)

        if item.assignee is not None and item.assignee != request.user:
            if new_assignee:
                return Response("This item has already been assigned", HTTP_400_BAD_REQUEST)
            else:
                return Response("You cannot unassign from another moderator", HTTP_400_BAD_REQUEST)

        item.assignee = new_assignee
        item.save(keep_deleted=True)

        if new_assignee and new_assignee != request.user:
            push_notification(
                [new_assignee],
                request.user,
                'equipment-item-assigned',
                {
                    'user': request.user.userprofile.get_display_name(),
                    'user_url': build_notification_url(
                        settings.BASE_URL + reverse('user_page', args=(request.user.username,))
                    ),
                    'item': f'{item.brand.name if item.brand else _("(DIY)")} {item.name}',
                    'item_url': build_notification_url(
                        AppRedirectionService.redirect(
                            f'/equipment/explorer/{EquipmentItemService(item).get_type()}/{item.pk}'
                        )
                    ),
                }
            )

        serializer = self.serializer_class(item)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def approve(self, request, pk):
        if not UserService(request.user).is_in_group(GroupName.EQUIPMENT_MODERATORS):
            raise PermissionDenied(request.user)

        item: EquipmentItem = get_object_or_404(self.get_serializer().Meta.model.objects, pk=pk)

        if item.reviewer_lock and item.reviewer_lock != request.user:
            return self._conflict_response()

        if item.reviewed_by is not None:
            return Response("This item was already reviewed", HTTP_400_BAD_REQUEST)

        if item.created_by == request.user:
            return Response("You cannot review an item that you created", HTTP_400_BAD_REQUEST)

        if item.assignee and item.assignee != request.user:
            return Response("You cannot review an item that is not assigned to you", HTTP_400_BAD_REQUEST)

        item.reviewed_by = request.user
        item.reviewed_timestamp = timezone.now()
        item.reviewer_decision = EquipmentItemReviewerDecision.APPROVED
        item.reviewer_comment = request.data.get('comment')
        item.assignee = None

        if item.created_by and item.created_by != request.user:
            push_notification(
                [item.created_by],
                request.user,
                'equipment-item-approved',
                {
                    'user': request.user.userprofile.get_display_name(),
                    'user_url': build_notification_url(
                        settings.BASE_URL + reverse('user_page', args=(request.user.username,))
                    ),
                    'item': f'{item.brand.name if item.brand else _("(DIY)")} {item.name}',
                    'item_url': build_notification_url(
                        AppRedirectionService.redirect(
                            f'/equipment/explorer/{EquipmentItemService(item).get_type()}/{item.pk}'
                        )
                    ),
                    'comment': item.reviewer_comment,
                }
            )

        item.save()

        serializer = self.serializer_class(item)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def unapprove(self, request, pk):
        if not UserService(request.user).is_in_group(GroupName.EQUIPMENT_MODERATORS):
            raise PermissionDenied(request.user)

        item: EquipmentItem = get_object_or_404(self.get_serializer().Meta.model.objects, pk=pk)

        if item.reviewer_lock and item.reviewer_lock != request.user:
            return self._conflict_response()

        if item.reviewed_by is None:
            return Response("This item was not already reviewed", HTTP_400_BAD_REQUEST)

        if item.created_by == request.user:
            return Response("You cannot review an item that you created", HTTP_400_BAD_REQUEST)

        item.reviewed_by = None
        item.reviewed_timestamp = None
        item.reviewer_decision = None
        item.reviewer_comment = None
        item.save()

        serializer = self.serializer_class(item)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def reject(self, request, pk):
        if not UserService(request.user).is_in_group(GroupName.EQUIPMENT_MODERATORS):
            raise PermissionDenied(request.user)

        ModelClass = self.get_serializer().Meta.model
        item: EquipmentItem = get_object_or_404(ModelClass.objects, pk=pk)

        if item.reviewer_lock and item.reviewer_lock != request.user:
            return self._conflict_response()

        if item.reviewed_by is not None and item.reviewer_decision == EquipmentItemReviewerDecision.APPROVED:
            return Response("This item was already approved", HTTP_400_BAD_REQUEST)

        if item.created_by == request.user:
            return Response("You cannot review an item that you created", HTTP_400_BAD_REQUEST)

        if item.assignee and item.assignee != request.user:
            return Response("You cannot review an item that is not assigned to you", HTTP_400_BAD_REQUEST)

        log.debug(f'{request.user.pk} requested rejection of item {ModelClass}/{pk}')

        item.reviewed_by = request.user
        item.reviewed_timestamp = timezone.now()
        item.reviewer_decision = EquipmentItemReviewerDecision.REJECTED
        item.reviewer_rejection_reason = request.data.get('reason')
        item.reviewer_comment = request.data.get('comment')
        item.reviewer_rejection_duplicate_of_klass = request.data.get('duplicate_of_klass', item.klass)
        item.reviewer_rejection_duplicate_of_usage_type = request.data.get('duplicate_of_usage_type')
        item.reviewer_rejection_duplicate_of = request.data.get('duplicate_of')
        item.assignee = None
        item.save(keep_deleted=True)

        reject_item.delay(item.id, item.klass)

        serializer = self.serializer_class(item)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'], url_path='freeze-as-ambiguous')
    def freeze_as_ambiguous(self, request, pk):
        if not UserService(request.user).is_in_group(GroupName.EQUIPMENT_MODERATORS):
            raise PermissionDenied(request.user)

        ModelClass = self.get_serializer().Meta.model
        item: EquipmentItem = get_object_or_404(ModelClass.objects, pk=pk)

        if item.reviewer_lock and item.reviewer_lock != request.user:
            return self._conflict_response()

        if not item.variants.all().exists():
            return Response("You cannot freeze as ambiguous an item with no variants", HTTP_400_BAD_REQUEST)

        EquipmentItemService(item).freeze_as_ambiguous()

        serializer = self.serializer_class(item)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'], url_path='unfreeze-as-ambiguous')
    def unfreeze_as_ambiguous(self, request, pk):
        if not UserService(request.user).is_in_group(GroupName.EQUIPMENT_MODERATORS):
            raise PermissionDenied(request.user)

        ModelClass = self.get_serializer().Meta.model
        item: EquipmentItem = get_object_or_404(ModelClass.objects, pk=pk)

        if item.reviewer_lock and item.reviewer_lock != request.user:
            return self._conflict_response()

        if item.frozen_as_ambiguous:
            item.frozen_as_ambiguous = None
            item.save(keep_deleted=True)

        serializer = self.serializer_class(item)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'], url_path='most-often-used-with')
    def most_often_used_with(self, request, pk: int) -> Response:
        valid_subscription = PremiumService(request.user).get_valid_usersubscription()
        can_access = can_access_full_search(valid_subscription)
        cache_key: str = f'equipment_item_view_set_{self.get_object().__class__.__name__}_{pk}_most_often_used_with_{can_access}'
        data = cache.get(cache_key)

        if data is None:
            sqs: SearchQuerySet = SearchQuerySet().models(self.get_serializer().Meta.model).filter(django_id=pk)

            if sqs.count() > 0:
                data = sqs[0].equipment_item_most_often_used_with
            else:
                data = '{}'

            if not can_access:
                # Restrict to the top item.
                parsed = dict(Counter(simplejson.loads(data)).most_common(1))
                data = simplejson.dumps(parsed)

            cache.set(cache_key, data, 60 * 60 * 12)

        return Response(simplejson.loads(data))

    @action(detail=True, methods=['GET'])
    def listings(self, request, pk: int) -> Response:
        ModelClass = self.get_serializer().Meta.model
        item: EquipmentItem = get_object_or_404(ModelClass.objects, pk=pk)

        valid_user_subscription = PremiumService(request.user).get_valid_usersubscription()
        allow_full_retailer_integration = PremiumService.allow_full_retailer_integration(valid_user_subscription, None)

        if not item.brand:
            # Nothing to do for DIY items
            return Response(dict(
                brand_listings=[],
                item_listings=[],
                allow_full_retailer_integration=allow_full_retailer_integration,
            ))

        country_code = get_client_country_code(request)
        brand_listings = EquipmentService.equipment_brand_listings_by_item(item, country_code)
        item_listings = EquipmentService.equipment_item_listings(item, country_code)

        return Response(
            dict(
                brand_listings=BrandListingSerializer(brand_listings, many=True).data,
                item_listings=ItemListingSerializer(item_listings, many=True).data,
                allow_full_retailer_integration=allow_full_retailer_integration,
            )
        )

    def image_upload(self, request, pk):
        obj = self.get_object()
        serializer = self.serializer_class(obj, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, HTTP_400_BAD_REQUEST)

    class Meta:
        abstract = True
