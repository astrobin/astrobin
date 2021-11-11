from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import TrigramDistance
from django.db.models import Q, Value
from django.db.models.functions import Lower, Concat
from django.urls import reverse
from django.utils import timezone
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from astrobin.models import Gear
from astrobin_apps_equipment.api.permissions.is_equipment_moderator_or_read_only import IsEquipmentModeratorOrReadOnly
from astrobin_apps_equipment.models import EquipmentItem
from astrobin_apps_equipment.services.equipment_item_service import EquipmentItemService
from astrobin_apps_notifications.utils import push_notification, build_notification_url
from common.services import AppRedirectionService


class EquipmentItemViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsEquipmentModeratorOrReadOnly]
    http_method_names = ['get', 'post', 'head']

    def get_queryset(self):
        q = self.request.GET.get('q')
        sort = self.request.GET.get('sort')

        manager = self.get_serializer().Meta.model.objects
        queryset = manager.all()

        if q:
            queryset = queryset.annotate(
                full_name=Concat('brand__name', Value(' '), 'name'),
                distance=TrigramDistance('full_name', q)
            ).filter(
                Q(distance__lte=.8) | Q(full_name__icontains=q)
            ).order_by(
                'distance'
            )[:10]
        elif sort == "az":
            queryset = queryset.order_by(Lower('brand__name'), Lower('name'))

        return queryset

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
            objects = manager \
                          .annotate(distance=TrigramDistance('name', q)) \
                          .filter(
                Q(brand=int(brand)) &
                Q(Q(distance__lte=.7) | Q(name__icontains=q)) &
                ~Q(name=q)) \
                          .order_by('distance')[:10]

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
            objects = manager.filter(brand=int(brand)).order_by('name')

        serializer = self.serializer_class(objects, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def approve(self, request, pk):
        item = get_object_or_404(self.get_serializer().Meta.model.objects, pk=pk)

        if item.reviewed_by is not None:
            return Response("This item was already reviewed", HTTP_400_BAD_REQUEST)

        if item.created_by == request.user:
            return Response("You cannot review an item that you created", HTTP_400_BAD_REQUEST)

        item.reviewed_by = request.user
        item.reviewed_timestamp = timezone.now()
        item.reviewer_decision = 'APPROVED'
        item.reviewer_comment = request.data.get('comment')

        if item.created_by:
            push_notification(
                [item.created_by],
                request.user,
                'equipment-item-approved',
                {
                    'user': request.user.userprofile.get_display_name(),
                    'user_url': build_notification_url(
                        settings.BASE_URL + reverse('user_page', args=(request.user.username,))),
                    'item': f'{item.brand.name} {item.name}',
                    'item_url': build_notification_url(
                        AppRedirectionService.redirect(
                            f'/equipment/explorer/{EquipmentItemService(item).get_type()}/{item.pk}')
                    ),
                    'comment': item.reviewer_comment,
                }
            )

        item.save()

        serializer = self.serializer_class(item)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def reject(self, request, pk):
        model = self.get_serializer().Meta.model
        item: EquipmentItem = get_object_or_404(model.objects, pk=pk)

        if item.reviewed_by is not None and item.reviewer_decision == 'APPROVED':
            return Response("This item was already approved", HTTP_400_BAD_REQUEST)

        if item.created_by == request.user:
            return Response("You cannot review an item that you created", HTTP_400_BAD_REQUEST)

        item.reviewed_by = request.user
        item.reviewed_timestamp = timezone.now()
        item.reviewer_decision = 'REJECTED'
        item.reviewer_rejection_reason = request.data.get('reason')
        item.reviewer_comment = request.data.get('comment')

        if item.created_by:
            push_notification(
                [item.created_by],
                request.user,
                'equipment-item-rejected',
                {
                    'user': request.user.userprofile.get_display_name(),
                    'user_url': build_notification_url(
                        settings.BASE_URL + reverse('user_page', args=(request.user.username,))),
                    'item': f'{item.brand.name} {item.name}',
                    'reject_reason': item.reviewer_rejection_reason,
                    'comment': item.reviewer_comment,
                }
            )

        item.name = '[DELETED] %s' % item.name
        item.save()
        item.delete()

        Gear.objects.filter(
            migration_flag='MIGRATE',
            migration_content_type=ContentType.objects.get_for_model(model),
            migration_object_id=item.id,
        ).update(
            migration_flag=None,
            migration_content_type=None,
            migration_object_id=None,
            migration_flag_moderator=None,
            migration_flag_moderator_lock=None,
            migration_flag_moderator_lock_timestamp=None,
            migration_flag_reviewer=None,
            migration_flag_reviewer_decision='REJECTED_BAD_MIGRATION_TARGET',
            migration_flag_reviewer_rejection_comment=request.data.get('comment')
        )

        serializer = self.serializer_class(item)
        return Response(serializer.data)

    def image_upload(self, request, pk):
        obj = self.get_object()
        serializer = self.serializer_class(obj, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, HTTP_400_BAD_REQUEST)

    class Meta:
        abstract = True
