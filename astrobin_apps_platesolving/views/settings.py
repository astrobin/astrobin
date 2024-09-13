from django.core.cache import cache
from django_filters.rest_framework import DjangoFilterBackend
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST

from astrobin_apps_platesolving.permissions.is_settings_solution_target_owner_or_readonly import IsSettingsSolutionTargetOwnerOrReadOnly
from astrobin_apps_platesolving.serializers import (
    PlateSolvingAdvancedSettingsSampleRawFrameFileSerializer, PlateSolvingAdvancedSettingsSerializer,
    PlateSolvingSettingsSerializer,
)
from astrobin_apps_platesolving.solver import Solver
from astrobin_apps_platesolving.tasks import start_basic_solver, start_advanced_solver


class PlateSolvingSettingsBaseViewSet(viewsets.ModelViewSet):
    filter_backends = (DjangoFilterBackend,)
    parser_classes = (CamelCaseJSONParser,)
    renderer_classes = (BrowsableAPIRenderer, CamelCaseJSONRenderer,)
    permission_classes = [IsSettingsSolutionTargetOwnerOrReadOnly]

    def get_queryset(self):
        solution_id = self.request.query_params.get('solution', None)
        if not solution_id:
            return self.get_serializer().Meta.model.objects.all()

        return self.get_serializer().Meta.model.objects.filter(solution__id=solution_id).select_related('solution')


class PlateSolvingSettingsViewSet(PlateSolvingSettingsBaseViewSet):
    serializer_class = PlateSolvingSettingsSerializer

    def perform_update(self, serializer):
        super().perform_update(serializer)
        settings = serializer.instance
        settings.refresh_from_db()
        solution = settings.solution
        solution.clear()
        cache.delete(f'astrobin_solution_{solution.content_type.model}_{solution.object_id}')

        start_basic_solver.delay(content_type_id=solution.content_type_id, object_id=solution.object_id)


class PlateSolvingAdvancedSettingsViewSet(PlateSolvingSettingsBaseViewSet):
    serializer_class = PlateSolvingAdvancedSettingsSerializer

    def perform_update(self, serializer):
        super().perform_update(serializer)
        settings = serializer.instance
        settings.refresh_from_db()
        solution = settings.solution
        solution.clear_advanced(save=True)

        if solution.status == Solver.SUCCESS:
            start_advanced_solver.delay(solution.id)
        else:
            start_basic_solver.delay(content_type_id=solution.content_type_id, object_id=solution.object_id)

    @action(
        detail=True,
        methods=['POST'],
        serializer_class=PlateSolvingAdvancedSettingsSampleRawFrameFileSerializer,
        parser_classes=[MultiPartParser, FormParser],
        url_path='sample-raw-frame-file'
    )
    def sample_raw_frame_file(self, request, pk):
        obj = self.get_object()
        serializer = self.serializer_class(obj, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, HTTP_400_BAD_REQUEST)
