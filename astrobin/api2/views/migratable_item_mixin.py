from django.http import HttpResponseBadRequest
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from astrobin.models import Gear
from astrobin_apps_equipment.models import Camera


class MigratableItemMixin:
    @action(detail=False, methods=['get'], url_path='random-non-migrated')
    def random_non_migrated(self, request):
        queryset = self.get_queryset().filter(migration_flag__isnull=True).order_by('?')[:1]
        serializer = self.get_serializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=['put'], url_path='set-migration')
    def set_migration(self, request, pk):
        obj = self.get_object()  # type: Gear

        migrationFlag = request.data.get('migrationFlag')
        itemType = request.data.get('itemType')
        itemId = request.data.get('itemId')
        item = None

        if migrationFlag not in ('WRONG_TYPE', 'MULTIPLE_ITEMS', 'DIY', 'MIGRATE'):
            return HttpResponseBadRequest('Bad migration flag')

        if migrationFlag == 'MIGRATE':
            if itemType is None or itemId is None:
                return HttpResponseBadRequest('When migration flag is MIGRATE, item type and item id are mandatory')

            if itemType == 'CAMERA':
                item = Camera.objects.get(pk=itemId)
            else:
                return HttpResponseBadRequest('Bad item type')

        obj.migration_flag = migrationFlag
        obj.migration_flag_moderator = request.user
        obj.migration_flag_timestamp = timezone.now()

        if item:
            obj.migration_content_object = item

        obj.save()

        return Response(status=200)
