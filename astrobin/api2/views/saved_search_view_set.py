from django.utils.translation import gettext_lazy
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import permissions, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.api2.serializers.saved_search_serializer import SavedSearchSerializer
from astrobin.models import SavedSearch
from common.permissions import IsObjectUser


class SavedSearchViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsObjectUser)
    serializer_class = SavedSearchSerializer
    ordering_fields = ('created_on', 'name', 'id')
    pagination_class = None
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]

    def get_queryset(self):
        return SavedSearch.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        max_searches = 20
        if SavedSearch.objects.filter(user=self.request.user).count() >= max_searches:
            raise ValidationError(
                gettext_lazy(
                    "You have reached the maximum number of saved searches. "
                    "Please delete some to make room for new ones."
                )
            )

        if SavedSearch.objects.filter(user=self.request.user, name=serializer.validated_data["name"]).exists():
            raise ValidationError(
                gettext_lazy("You already have a saved search with this name.")
            )

        serializer.save(user=self.request.user)
