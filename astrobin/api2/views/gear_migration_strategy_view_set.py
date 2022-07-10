# -*- coding: utf-8 -*-
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from django.utils import timezone
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin.api2.serializers.gear_migration_strategy_serializer import GearMigrationStrategySerializer
from astrobin.models import GearMigrationStrategy
from astrobin.services.gear_service import GearService
from astrobin_apps_equipment.api.permissions.is_equipment_moderator_or_own_migrator_or_readonly import \
    IsEquipmentModeratorOrOwnMigratorOrReadOnly
from astrobin_apps_equipment.services import EquipmentService
from common.constants import GroupName


class GearMigrationStrategyViewSet(viewsets.ModelViewSet):
    serializer_class = GearMigrationStrategySerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [IsEquipmentModeratorOrOwnMigratorOrReadOnly]
    http_method_names = ['get', 'head', 'options', 'put']

    def get_queryset(self) -> QuerySet:
        queryset: QuerySet = GearMigrationStrategy.objects.all()

        if self.request.query_params.get('pending-review', 'false').lower() in ('1', 'true', 'yes'):
            queryset = queryset.filter(
                Q(user__isnull=True) &
                Q(migration_flag_reviewer__isnull=True) &
                Q(
                    Q(migration_flag_reviewer_lock__isnull=True) |
                    Q(migration_flag_reviewer_lock=self.request.user)
                ) &
                ~Q(migration_flag_moderator=self.request.user)
            )

        queryset = queryset.filter(
            Q(migration_flag__in=['WRONG_TYPE', 'MULTIPLE_ITEMS', 'NOT_ENOUGH_INFO', 'MIGRATE']) &
            Q(
                Q(migration_flag_moderator=self.request.user) |
                Q(user=self.request.user)
            )
        )

        if self.request.user.groups.filter(name=GroupName.EQUIPMENT_MODERATORS).exists():
            queryset = queryset.filter(user__isnull=True)

        return queryset.distinct()

    @action(detail=True, methods=['put'], url_path='lock-for-migration-review')
    def lock_for_migration_review(self, request: HttpRequest, pk: int) -> Response:
        if not request.user.groups.filter(name=GroupName.EQUIPMENT_MODERATORS).exists():
            raise PermissionDenied(request.user)

        strategy: GearMigrationStrategy = self.get_object()

        if strategy.gear.migration_flag_moderator_lock not in (None, request.user):
            return Response(status=409)

        if strategy.migration_flag_reviewer_lock not in (None, request.user):
            return Response(status=409)

        strategy.migration_flag_reviewer_lock = request.user
        strategy.migration_flag_reviewer_lock_timestamp = timezone.now()
        strategy.save()

        serializer = self.get_serializer(strategy)
        return Response(serializer.data)

    @action(detail=True, methods=['put'], url_path='release-lock-for-migration-review')
    def release_lock_for_migration_review(self, request: HttpRequest, pk: int) -> Response:
        if not request.user.groups.filter(name=GroupName.EQUIPMENT_MODERATORS).exists():
            raise PermissionDenied(request.user)

        strategy: GearMigrationStrategy = self.get_object()

        if strategy.migration_flag_reviewer_lock not in (None, request.user):
            raise PermissionDenied

        strategy.migration_flag_reviewer_lock = None
        strategy.migration_flag_reviewer_lock_timestamp = None
        strategy.save()

        serializer = self.get_serializer(strategy)
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    def approve(self, request, pk):
        if not request.user.groups.filter(name=GroupName.EQUIPMENT_MODERATORS).exists():
            raise PermissionDenied(request.user)

        strategy: GearMigrationStrategy = self.get_object()

        if strategy.migration_flag is None:
            return Response(status=409)

        if request.user == strategy.migration_flag_moderator:
            raise PermissionDenied

        strategy = GearService.approve_migration_strategy(
            strategy, request.user, request.data.get('reason'), request.data.get('comment')
        )

        serializer = self.get_serializer(strategy)
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    def reject(self, request, pk):
        if not request.user.groups.filter(name=GroupName.EQUIPMENT_MODERATORS).exists():
            raise PermissionDenied(request.user)

        strategy: GearMigrationStrategy = self.get_object()

        if strategy.migration_flag is None:
            return Response(status=409)

        if request.user == strategy.migration_flag_moderator:
            raise PermissionDenied

        strategy = GearService.reject_migration_strategy(
            strategy, request.user, request.data.get('reason'), request.data.get('comment')
        )

        serializer = self.get_serializer(strategy)
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    def undo(self, request, pk):
        strategy: GearMigrationStrategy = self.get_object()

        if strategy.migration_flag is None:
            return Response(status=409)

        if (
                strategy.user != request.user and
                strategy.migration_flag_moderator != request.user and
                not request.user.is_superuser
        ):
            raise PermissionDenied(request.user)

        EquipmentService.undo_migration_strategy(strategy)

        return Response(status=200)

