from rest_framework.decorators import action
from rest_framework.response import Response


class MigratableItemMixin:
    @action(detail=False, methods=['get'], url_path='random-non-migrated')
    def random_non_migrated(self, request):
        queryset = self.get_queryset().filter(migration_flag__isnull=True).order_by('?')[:1]
        serializer = self.get_serializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=['put'], url_path='set-migration')
    def set_migration(self, request):
        # TODO
        obj = self.get_object()
        return Response()
