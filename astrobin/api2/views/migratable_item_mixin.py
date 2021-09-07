from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpRequest
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
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

    @action(detail=False, methods=['get'], url_path='random-non-migrated')
    def random_non_migrated(self, request):
        queryset = self.__random_non_migrated_queryset(request.user).order_by('?')[:1]
        serializer = self.get_serializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='non-migrated-count')
    def non_migrated_count(self, request):
        return Response(self.__random_non_migrated_queryset(request.user).count())

    @action(detail=False, methods=['get'], url_path='pending-migration-review')
    def pending_migration_review(self, request):
        queryset = self.get_queryset()\
            .filter(migration_flag__isnull=False, migration_flag_reviewer__isnull=True)\
            .order_by('migration_flag_timestamp')[:50]
        serializer = self.get_serializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=['put'], url_path='lock-for-migration')
    def lock_for_migration(self, request: HttpRequest, pk: int) -> Response:
        obj: Gear = self.get_object()

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

    @action(detail=True, methods=['put'], url_path='accept-migration')
    def accept_migration(self, request, pk):
        obj: Gear = self.get_object()

        if not request.user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied

        if obj.migration_flag is None:
            return Response(status=409)

        if request.user == obj.migration_flag_moderator:
            raise PermissionDenied

        obj.migration_flag_reviewer = request.user
        obj.save()

        serializer = self.get_serializer(obj)
        return Response(serializer.data)
