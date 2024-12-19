import base64
import logging
import urllib.error
import urllib.parse
import urllib.request
import uuid

from dateutil import parser
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import base
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import generics
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from astrobin_apps_platesolving.api_filters.advanced_task_filter import AdvancedTaskFilter
from astrobin_apps_platesolving.api_filters.solution_list_filter import SolutionListFilter
from astrobin_apps_platesolving.models import PlateSolvingAdvancedLiveLogEntry, PlateSolvingAdvancedTask, Solution
from astrobin_apps_platesolving.permissions.is_solution_target_owner_or_readonly import IsSolutionTargetOwnerOrReadOnly
from astrobin_apps_platesolving.serializers import AdvancedTaskSerializer, SolutionSerializer
from astrobin_apps_platesolving.services import SolutionService
from astrobin_apps_platesolving.solver import Solver
from astrobin_apps_platesolving.utils import corrected_pixscale
from common.permissions import ReadOnly
from common.utils import lock_table

log = logging.getLogger(__name__)


class SolutionPixInsightNextTask(base.View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SolutionPixInsightNextTask, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        username = request.POST.get('userName')
        password = request.POST.get('userPassword')

        if username != settings.PIXINSIGHT_USERNAME or password != settings.PIXINSIGHT_PASSWORD:
            return HttpResponseForbidden()

        with lock_table(PlateSolvingAdvancedTask):
            task = PlateSolvingAdvancedTask.objects.filter(active=True).order_by('-created').last()

            if task is None:
                return HttpResponse('')

            task.active = False
            task.save()

        response = \
            'OK\n' \
            'serialNumber=%s\n' \
            'taskType=%s\n' \
            'taskParams=%s\n' \
            'requestUser=%s\n' \
            'requestUTC=%s\n' \
            'callbackURL=%s\n' % (
                task.serial_number,
                'ASTROBIN_SVG_OVERLAY',
                task.task_params,
                username,
                task.created,
                settings.BASE_URL + reverse('astrobin_apps_platesolving.pixinsight_webhook')
            )

        log.info("PixInsight next-task: sending response\n%s" % response)

        return HttpResponse(response)


class SolutionPixInsightWebhook(base.View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SolutionPixInsightWebhook, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        serial_number = request.POST.get('serialNumber')
        status = request.POST.get('status', 'ERROR')
        error_message = request.POST.get('errorMessage')

        log.debug("PixInsight Webhook called for %s: %s" % (serial_number, status))

        PlateSolvingAdvancedTask.objects.filter(serial_number=serial_number).update(
            status=status,
            error_message=error_message,
        )

        solution = get_object_or_404(Solution, pixinsight_serial_number=serial_number)

        if status == 'OK':
            svg_hd = request.POST.get('svgAnnotation')
            svg_regular = request.POST.get('svgAnnotationSmall', svg_hd)
            pixscale = request.POST.get('resolution')
            finding_chart = request.POST.get('findingChart')
            finding_chart_small = request.POST.get('findingChartSmall')

            if svg_hd:
                solution.pixinsight_svg_annotation_hd.save(serial_number + ".svg", ContentFile(svg_hd.encode('utf-8')))

            if svg_regular:
                solution.pixinsight_svg_annotation_regular.save(
                    serial_number + ".svg", ContentFile(svg_regular.encode('utf-8'))
                )

            if finding_chart:
                data = base64.b64decode(urllib.parse.unquote(finding_chart))
                solution.pixinsight_finding_chart = ContentFile(data, name=f'{uuid.uuid4()}.png')

            if finding_chart_small:
                data = base64.b64decode(urllib.parse.unquote(finding_chart_small))
                solution.pixinsight_finding_chart_small = ContentFile(data, name=f'{uuid.uuid4()}.png')

            solution.status = Solver.ADVANCED_SUCCESS

            solution.advanced_ra = request.POST.get('centerRA')
            solution.advanced_ra_top_left = request.POST.get('topLeftRA')
            solution.advanced_ra_top_right = request.POST.get('topRightRA')
            solution.advanced_ra_bottom_left = request.POST.get('bottomLeftRA')
            solution.advanced_ra_bottom_right = request.POST.get('bottomRightRA')

            solution.advanced_dec = request.POST.get('centerDec')
            solution.advanced_dec_top_left = request.POST.get('topLeftDec')
            solution.advanced_dec_top_right = request.POST.get('topRightDec')
            solution.advanced_dec_bottom_left = request.POST.get('bottomLeftDec')
            solution.advanced_dec_bottom_right = request.POST.get('bottomRightDec')

            solution.advanced_orientation = request.POST.get('rotation')
            solution.advanced_pixscale = pixscale \
                if solution.advanced_settings and solution.advanced_settings.sample_raw_frame_file \
                else corrected_pixscale(solution, pixscale)
            solution.advanced_flipped = request.POST.get('flipped') == 'true'
            solution.advanced_wcs_transformation = request.POST.get('wcsTransformation')

            solution.advanced_matrix_rect = request.POST.get('matrixRect')
            solution.advanced_matrix_delta = request.POST.get('matrixDelta')
            solution.advanced_ra_matrix = request.POST.get('raMatrix')
            solution.advanced_dec_matrix = request.POST.get('decMatrix')

            solution.advanced_annotations = request.POST.get('labelInfo')
            solution.advanced_annotations_regular = request.POST.get('labelInfoSmall')
        else:
            solution.status = Solver.ADVANCED_FAILED
            log.error(request.POST.get('errorMessage', 'Unknown error'))

        solution.save()

        return HttpResponse("OK")


class SolutionPixInsightLiveLogWebhook(base.View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SolutionPixInsightLiveLogWebhook, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        serial_number = request.POST.get('serialNumber')
        timestamp = request.POST.get('timestamp')
        stage = request.POST.get('stage')
        log = request.POST.get('log')

        if None in (serial_number, timestamp, stage):
            return HttpResponseBadRequest("The following arguments are mandatory: serialNumber, timestamp, stage.")

        PlateSolvingAdvancedLiveLogEntry.objects.create(
            serial_number=serial_number,
            timestamp=parser.parse(timestamp),
            stage=stage,
            log=log,
        )

        return HttpResponse("OK")


###############################################################################
# API                                                                         #
###############################################################################


class SolutionList(generics.ListCreateAPIView):
    model = Solution
    queryset = Solution.objects.order_by('pk')
    serializer_class = SolutionSerializer
    permission_classes = (IsSolutionTargetOwnerOrReadOnly,)
    filter_class = SolutionListFilter
    pagination_class = None

    def list(self, request, *args, **kwargs):
        object_ids = request.query_params.get('object_ids')
        max_object_ids = 100
        if object_ids:
            object_ids = object_ids.split(',')
            if len(object_ids) > max_object_ids:
                return HttpResponseBadRequest(f'Please do not request more than {max_object_ids} object ids.')
        return super().list(request, *args, **kwargs)


class SolutionDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Solution
    serializer_class = SolutionSerializer
    permission_classes = (IsSolutionTargetOwnerOrReadOnly,)
    queryset = Solution.objects.all()


class SolutionRestartView(APIView):
    permission_classes = (IsSolutionTargetOwnerOrReadOnly,)

    def patch(self, request, pk):
        solution = Solution.objects.get(pk=pk)
        SolutionService(solution).restart()
        solution.refresh_from_db()
        return Response(SolutionSerializer(solution).data, status=HTTP_200_OK)


class SolutionPixInsightMatrix(APIView):
    permission_classes = (ReadOnly,)

    def get(self, request, pk):
        solution = Solution.objects.get(pk=pk)
        matrix = {
            'matrixRect': solution.advanced_matrix_rect,
            'matrixDelta': solution.advanced_matrix_delta,
            'raMatrix': solution.advanced_ra_matrix,
            'decMatrix': solution.advanced_dec_matrix,
        }
        return Response(matrix)


class AdvancedTaskList(generics.ListAPIView):
    model = PlateSolvingAdvancedTask
    queryset = PlateSolvingAdvancedTask.objects.order_by('-created')
    serializer_class = AdvancedTaskSerializer
    permission_classes = (ReadOnly,)
    filter_class = AdvancedTaskFilter
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
