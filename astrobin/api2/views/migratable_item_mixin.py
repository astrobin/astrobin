from rest_framework.decorators import list_route
from rest_framework.response import Response


class MigratableItemMixin:
    @list_route(url_path='random-non-migrated')
    def random_non_migrated(self, request):
        queryset = self.get_queryset().filter(migration_flag__isnull=True).order_by('?')[:1]
        serializer = self.get_serializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)
