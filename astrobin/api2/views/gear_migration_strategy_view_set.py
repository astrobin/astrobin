# -*- coding: utf-8 -*-
from django.conf import settings
from django.db.models import QuerySet, Q
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin.api2.serializers.gear_migration_strategy_serializer import GearMigrationStrategySerializer
from astrobin.models import GearMigrationStrategy
from astrobin_apps_equipment.api.permissions.is_equipment_moderator_or_read_only import IsEquipmentModeratorOrReadOnly
from astrobin_apps_notifications.utils import push_notification, build_notification_url
from common.services import AppRedirectionService


class GearMigrationStrategyViewSet(viewsets.ModelViewSet):
    serializer_class = GearMigrationStrategySerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [IsEquipmentModeratorOrReadOnly]
    http_method_names = ['get', 'head', 'options', 'put']

    def get_queryset(self) -> QuerySet:
        queryset: QuerySet = GearMigrationStrategy.objects.all()

        if self.request.query_params.get('pending-review', 'false').lower() in ('1', 'true', 'yes'):
            queryset = queryset.filter(
                Q(migration_flag_reviewer=None) &
                Q(
                    Q(migration_flag_reviewer_lock__isnull=True) |
                    Q(migration_flag_reviewer_lock=self.request.user)
                ) &
                ~Q(migration_flag_moderator=self.request.user)
            )

        return queryset

    @action(detail=True, methods=['put'], url_path='lock-for-migration-review')
    def lock_for_migration_review(self, request: HttpRequest, pk: int) -> Response:
        if not request.user.groups.filter(name='equipment_moderators').exists():
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
        if not request.user.groups.filter(name='equipment_moderators').exists():
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
        if not request.user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied(request.user)

        strategy: GearMigrationStrategy = self.get_object()

        if strategy.migration_flag is None:
            return Response(status=409)

        if request.user == strategy.migration_flag_moderator:
            raise PermissionDenied

        strategy.migration_flag_reviewer = request.user
        strategy.migration_flag_reviewer_decision = 'APPROVED'
        strategy.migration_flag_reviewer_rejection_comment = None
        strategy.migration_flag_reviewer_lock = None
        strategy.migration_flag_reviewer_lock_timestamp = None
        strategy.save()

        strategy.gear.migration_flag_moderator_lock = None
        strategy.gear.migration_flag_moderator_lock_timestamp = None
        strategy.gear.save()

        target = strategy.migration_content_object

        push_notification(
            [strategy.migration_flag_moderator],
            request.user,
            'equipment-item-migration-approved',
            {
                'user': request.user.userprofile.get_display_name(),
                'user_url': build_notification_url(
                    settings.BASE_URL + reverse('user_page', args=(request.user.username,))),
                'migration_flag': strategy.migration_flag,
                'reason': request.data.get('reason'),
                'comment': request.data.get('comment'),
                'legacy_item': strategy.gear,
                'target_item': f'{target.brand.name} {target.name}' if target else None,
                'target_url': build_notification_url(
                    AppRedirectionService.redirect(
                        f'/equipment'
                        f'/explorer'
                        f'/{target.item_type}/{target.pk}'
                        f'/{target.slug}'
                    )
                ) if target else None,
            }
        )

        serializer = self.get_serializer(strategy)
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    def reject(self, request, pk):
        if not request.user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied(request.user)

        strategy: GearMigrationStrategy = self.get_object()

        if strategy.migration_flag is None:
            return Response(status=409)

        if request.user == strategy.migration_flag_moderator:
            raise PermissionDenied

        target = strategy.migration_content_object

        push_notification(
            [strategy.migration_flag_moderator],
            request.user,
            'equipment-item-migration-rejected',
            {
                'user': request.user.userprofile.get_display_name(),
                'user_url': build_notification_url(
                    settings.BASE_URL + reverse('user_page', args=(request.user.username,))),
                'migration_flag': strategy.migration_flag,
                'reason': request.data.get('reason'),
                'comment': request.data.get('comment'),
                'legacy_item': strategy.gear,
                'target_item': f'{target.brand.name} {target.name}' if target else None,
                'target_url': build_notification_url(
                    AppRedirectionService.redirect(
                        f'/equipment'
                        f'/explorer'
                        f'/{target.item_type}/{target.pk}'
                        f'/{target.slug}'
                    )
                ) if target else None,
                'migration_tool_url': build_notification_url(
                    AppRedirectionService.redirect(
                        f'/equipment'
                        f'/migration-tool'
                    )
                ) if target else None,
            }
        )

        strategy.gear.migration_flag_moderator_lock = None
        strategy.gear.migration_flag_moderator_lock_timestamp = None
        strategy.gear.save()

        strategy.delete()

        serializer = self.get_serializer(strategy)
        return Response(serializer.data)
