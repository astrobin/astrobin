from typing import List

from django.contrib.auth.models import User
from django.contrib.postgres.search import TrigramDistance
from django.db.models import Q, QuerySet, Count
from django.http import HttpResponseBadRequest, HttpRequest
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from astrobin.models import Gear, Filter, UserProfile, GearMigrationStrategy
from astrobin_apps_equipment.models import Camera, Telescope, Mount, Accessory, Software


class MigratableItemMixin:
    def __check_permissions(self, user: User, allow_own_equipment_migrators: bool = False):
        if not user.is_authenticated:
            raise PermissionDenied

        if allow_own_equipment_migrators:
            if not user.groups.filter(name__in=['equipment_moderators', 'own_equipment_migrators']).exists():
                raise PermissionDenied
        else:
            if not user.groups.filter(name='equipment_moderators').exists():
                raise PermissionDenied


    def __filter_by_user_items(self, queryset: QuerySet, user: User) -> QuerySet:
        profile: UserProfile = user.userprofile

        itemPks: List[int] = []
        itemPks.extend([x.pk for x in profile.telescopes.all()])
        itemPks.extend([x.pk for x in profile.cameras.all()])
        itemPks.extend([x.pk for x in profile.mounts.all()])
        itemPks.extend([x.pk for x in profile.filters.all()])
        itemPks.extend([x.pk for x in profile.accessories.all()])
        itemPks.extend([x.pk for x in profile.software.all()])

        return queryset.filter(pk__in=itemPks)

    def __random_non_migrated_queryset(self, user: User, global_results: bool) -> QuerySet:
        if global_results and not user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied(
                "You are not part of the 'equipment_moderators' group and cannot access the global non-migrated items"
            )

        if global_results:
            return self.get_queryset().annotate(count=Count('migration_strategies')).filter(
                Q(
                    Q(count=0) |
                    Q(
                        Q(count__gt=0) &
                        Q(migration_strategies__user__isnull=True)
                    )
                ) &
                Q(
                    Q(migration_flag_moderator_lock__isnull=True) |
                    Q(migration_flag_moderator_lock=user)
                )
            )

        queryset: QuerySet = self.get_queryset().annotate(count=Count('migration_strategies')).filter(
            Q(
                Q(count=0) |
                Q(
                    Q(count__gt=0) &
                    ~Q(migration_strategies__user=user) &
                    Q(migration_strategies__user__isnull=False)
                )
            ) &
            Q(
                Q(migration_flag_moderator_lock__isnull=True) |
                Q(migration_flag_moderator_lock=user)
            )
        )

        return self.__filter_by_user_items(queryset, user)

    def __similar_non_migrated(self, request, make, name, pk=None):
        try:
            max_distance = float(request.GET.get('max-distance', .7))
        except ValueError:
            max_distance = .7

        limit = request.GET.get('limit', 100)

        queryset = self.__random_non_migrated_queryset(request.user, 'global' in request.GET) \
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
        self.__check_permissions(request.user, allow_own_equipment_migrators=True)
        queryset = self.__random_non_migrated_queryset(request.user, 'global' in request.GET).order_by('?')[:1]
        serializer = self.get_serializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='non-migrated-count')
    def non_migrated_count(self, request):
        self.__check_permissions(request.user, allow_own_equipment_migrators=True)
        return Response(self.__random_non_migrated_queryset(request.user, 'global' in request.GET).count())

    @action(detail=True, methods=['get'], url_path='similar-non-migrated')
    def similar_non_migrated(self, request, pk):
        self.__check_permissions(request.user, allow_own_equipment_migrators=True)
        manager = self.get_serializer().Meta.model.objects
        obj = get_object_or_404(manager, pk=pk)

        return self.__similar_non_migrated(request, obj.make, obj.name, pk)

    @action(detail=False, methods=['get'], url_path='similar-non-migrated')
    def similar_non_migrated_by_make_and_name(self, request):
        self.__check_permissions(request.user, allow_own_equipment_migrators=True)
        return self.__similar_non_migrated(request, request.GET.get('make'), request.GET.get('name'))

    @action(detail=True, methods=['put'], url_path='lock-for-migration')
    def lock_for_migration(self, request: HttpRequest, pk: int) -> Response:
        self.__check_permissions(request.user, allow_own_equipment_migrators=True)

        obj: Gear = self.get_object()
        global_migration = request.user.groups.filter(name='equipment_moderators').exists()

        if global_migration and GearMigrationStrategy.objects.filter(gear=obj, user__isnull=True).exists():
            return Response(status=409)

        if not global_migration and GearMigrationStrategy.objects.filter(gear=obj, user=request.user).exists():
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
        self.__check_permissions(request.user, allow_own_equipment_migrators=True)

        obj: Gear = self.get_object()

        if obj.migration_flag_moderator_lock not in (None, request.user):
            raise PermissionDenied

        obj.migration_flag_moderator_lock = None
        obj.migration_flag_moderator_lock_timestamp = None
        obj.save()

        serializer = self.get_serializer(obj)
        return Response(serializer.data)

    @action(detail=True, methods=['put'], url_path='set-migration')
    def set_migration(self, request, pk):
        self.__check_permissions(request.user, allow_own_equipment_migrators=True)

        obj: Gear = self.get_object()
        global_migration = request.user.groups.filter(name='equipment_moderators').exists()

        if global_migration and GearMigrationStrategy.objects.filter(gear=obj, user__isnull=True).exists():
            return Response(status=409)

        if not global_migration and GearMigrationStrategy.objects.filter(gear=obj, user=request.user).exists():
            return Response(status=409)

        migration_flag = request.data.get('migrationFlag')
        item_type = request.data.get('itemType')
        item_id = request.data.get('itemId')
        item = None

        if migration_flag not in ('WRONG_TYPE', 'MULTIPLE_ITEMS', 'DIY', 'NOT_ENOUGH_INFO', 'MIGRATE'):
            return HttpResponseBadRequest('Bad migration flag')

        if migration_flag == 'MIGRATE':
            if item_type is None or item_id is None:
                return HttpResponseBadRequest('When migration flag is MIGRATE, item type and item id are mandatory')

            if item_type == 'CAMERA':
                item = Camera.objects.get(pk=item_id)
            elif item_type == 'TELESCOPE':
                item = Telescope.objects.get(pk=item_id)
            elif item_type == 'MOUNT':
                item = Mount.objects.get(pk=item_id)
            elif item_type == 'FILTER':
                item = Filter.objects.get(pk=item_id)
            elif item_type == 'ACCESSORY':
                item = Accessory.objects.get(pk=item_id)
            elif item_type == 'SOFTWARE':
                item = Software.objects.get(pk=item_id)
            else:
                return HttpResponseBadRequest('Bad item type')

        GearMigrationStrategy.objects.create(
            gear=obj,
            user=None if global_migration else request.user,
            migration_flag=migration_flag,
            migration_flag_moderator=request.user,
            migration_flag_timestamp=timezone.now(),
            migration_content_object=item,
        )

        obj.migration_flag_moderator_lock = None
        obj.migration_flag_moderator_lock_timestamp = None
        obj.save()

        serializer = self.get_serializer(obj)
        return Response(serializer.data)
