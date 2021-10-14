from django.contrib.postgres.search import TrigramDistance
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpRequest
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from astrobin.models import Gear
from astrobin_apps_equipment.models import Camera, Telescope


class MigratableItemMixin:
    def __random_non_migrated_queryset(self, user):
        return self.get_queryset().filter(
            Q(migration_flag__isnull=True) &
            Q(
                Q(migration_flag_moderator_lock__isnull=True) |
                Q(migration_flag_moderator_lock=user)
            )
        )

    def __similar_non_migrated(self, request, make, name, pk=None):
        if not request.user.is_authenticated:
            raise PermissionDenied

        if not request.user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied

        try:
            max_distance = float(request.GET.get('max-distance', .7))
        except ValueError:
            max_distance = .7

        limit = request.GET.get('limit', 100)
        manager = self.get_serializer().Meta.model.objects

        queryset = self.__random_non_migrated_queryset(request.user) \
            .annotate(name_distance=TrigramDistance('name', name),
                      make_distance=TrigramDistance('make', make)) \
            .filter(Q(name_distance__lte=max_distance) & Q(make_distance__lte=max_distance))

        if pk:
            queryset = queryset.exclude(pk=pk)

        queryset = queryset.order_by('name_distance')[:limit]

        serializer = self.get_serializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='random-non-migrated')
    def random_non_migrated(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied

        if not request.user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied

        queryset = self.__random_non_migrated_queryset(request.user).order_by('?')[:1]
        serializer = self.get_serializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='non-migrated-count')
    def non_migrated_count(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied

        if not request.user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied

        return Response(self.__random_non_migrated_queryset(request.user).count())

    @action(detail=False, methods=['get'], url_path='pending-migration-review')
    def pending_migration_review(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied

        if not request.user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied

        queryset = \
            self.get_queryset() \
                .filter(
                Q(migration_flag__isnull=False) &
                Q(migration_flag_reviewer__isnull=True) &
                Q(
                    Q(migration_flag_reviewer_lock__isnull=True) |
                    Q(migration_flag_reviewer_lock=request.user)
                ) &
                ~Q(migration_flag_moderator=request.user)
            ) \
                .order_by('migration_flag_timestamp')[:50]
        serializer = self.get_serializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='similar-non-migrated')
    def similar_non_migrated(self, request, pk):
        manager = self.get_serializer().Meta.model.objects
        obj = get_object_or_404(manager, pk=pk)

        return self.__similar_non_migrated(request, obj.make, obj.name, pk)

    @action(detail=False, methods=['get'], url_path='similar-non-migrated')
    def similar_non_migrated_by_make_and_name(self, request):
        return self.__similar_non_migrated(request, request.GET.get('make'), request.GET.get('name'))

    @action(detail=True, methods=['put'], url_path='lock-for-migration')
    def lock_for_migration(self, request: HttpRequest, pk: int) -> Response:
        obj: Gear = self.get_object()

        if not request.user.is_authenticated:
            raise PermissionDenied

        if not request.user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied

        if obj.migration_flag is not None:
            return Response(status=409)

        if obj.migration_flag_moderator_lock not in (None, request.user):
            return Response(status=409)

        obj.migration_flag_moderator_lock = request.user
        obj.migration_flag_moderator_lock_timestamp = timezone.now()

        obj.save()

        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=True, methods=['put'], url_path='release-lock-for-migration')
    def release_lock_for_migration(self, request: HttpRequest, pk: int) -> Response:
        obj: Gear = self.get_object()

        if not request.user.is_authenticated:
            raise PermissionDenied

        if not request.user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied

        if obj.migration_flag_moderator_lock is None:
            return Response(status=409)

        obj.migration_flag_moderator_lock = None
        obj.migration_flag_moderator_lock_timestamp = None

        obj.save()

        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=True, methods=['put'], url_path='lock-for-migration-review')
    def lock_for_migration_review(self, request: HttpRequest, pk: int) -> Response:
        obj: Gear = self.get_object()

        if not request.user.is_authenticated:
            raise PermissionDenied

        if not request.user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied

        if obj.migration_flag is None:
            return Response(status=409)

        if obj.migration_flag_reviewer_lock not in (None, request.user):
            return Response(status=409)

        obj.migration_flag_reviewer_lock = request.user
        obj.migration_flag_reviewer_lock_timestamp = timezone.now()

        obj.save()

        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=True, methods=['put'], url_path='release-lock-for-migration-review')
    def release_lock_for_migration_review(self, request: HttpRequest, pk: int) -> Response:
        obj: Gear = self.get_object()

        if not request.user.is_authenticated:
            raise PermissionDenied

        if not request.user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied

        if obj.migration_flag_reviewer_lock is None:
            return Response(status=409)

        obj.migration_flag_reviewer_lock = None
        obj.migration_flag_reviewer_lock_timestamp = None

        obj.save()

        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=True, methods=['put'], url_path='set-migration')
    def set_migration(self, request, pk):
        obj: Gear = self.get_object()

        if not request.user.is_authenticated:
            raise PermissionDenied

        if not request.user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied

        if obj.migration_flag is not None:
            return Response(status=409)

        migrationFlag = request.data.get('migrationFlag')
        itemType = request.data.get('itemType')
        itemId = request.data.get('itemId')
        item = None

        if migrationFlag not in ('WRONG_TYPE', 'MULTIPLE_ITEMS', 'DIY', 'NOT_ENOUGH_INFO', 'MIGRATE'):
            return HttpResponseBadRequest('Bad migration flag')

        if migrationFlag == 'MIGRATE':
            if itemType is None or itemId is None:
                return HttpResponseBadRequest('When migration flag is MIGRATE, item type and item id are mandatory')

            if itemType == 'CAMERA':
                item = Camera.objects.get(pk=itemId)
            elif itemType == 'TELESCOPE':
                item = Telescope.objects.get(pk=itemId)
            else:
                return HttpResponseBadRequest('Bad item type')

        obj.migration_flag = migrationFlag
        obj.migration_flag_moderator = request.user
        obj.migration_flag_timestamp = timezone.now()

        if item:
            obj.migration_content_object = item

        obj.save()

        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=True, methods=['put'], url_path='approve-migration')
    def approve_migration(self, request, pk):
        obj: Gear = self.get_object()

        if not request.user.is_authenticated:
            raise PermissionDenied

        if not request.user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied

        if obj.migration_flag is None:
            return Response(status=409)

        if request.user == obj.migration_flag_moderator:
            raise PermissionDenied

        obj.migration_flag_reviewer = request.user
        obj.migration_flag_reviewer_decision = 'APPROVED'
        obj.migration_flag_reviewer_rejection_comment = None
        obj.save()

        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=True, methods=['put'], url_path='reject-migration')
    def reject_migration(self, request, pk):
        obj: Gear = self.get_object()

        if not request.user.is_authenticated:
            raise PermissionDenied

        if not request.user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied

        if obj.migration_flag is None:
            return Response(status=409)

        if request.user == obj.migration_flag_moderator:
            raise PermissionDenied

        obj.migration_flag = None
        obj.migration_flag_timestamp = None
        obj.migration_content_type = None
        obj.migration_object_id = None
        obj.migration_flag_moderator = None
        obj.migration_flag_moderator_lock = None
        obj.migration_flag_moderator_lock_timestamp = None
        obj.migration_flag_reviewer = None
        obj.migration_flag_reviewer_decision = request.data.get('reason')
        obj.migration_flag_reviewer_rejection_comment = request.data.get('comment')

        obj.save()

        serializer = self.get_serializer(obj)
        return Response(serializer.data)
