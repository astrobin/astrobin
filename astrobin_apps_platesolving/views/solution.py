import logging
import os
import time
import urllib2

import simplejson
from braces.views import CsrfExemptMixin
from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.temp import NamedTemporaryFile
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import base
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework import permissions

from astrobin.models import DeepSky_Acquisition
from astrobin.utils import degrees_minutes_seconds_to_decimal_degrees
from astrobin_apps_platesolving.annotate import Annotator
from astrobin_apps_platesolving.api_filters.image_object_id_filter import ImageObjectIdFilter
from astrobin_apps_platesolving.models import PlateSolvingAdvancedSettings, PlateSolvingAdvancedTask
from astrobin_apps_platesolving.models import PlateSolvingSettings
from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.serializers import SolutionSerializer
from astrobin_apps_platesolving.solver import Solver, AdvancedSolver, SolverBase
from astrobin_apps_platesolving.utils import ThumbnailNotReadyException, get_target, get_solution, corrected_pixscale

log = logging.getLogger('apps')


class SolveView(base.View):
    def post(self, request, *args, **kwargs):
        target = get_target(kwargs.get('object_id'), kwargs.get('content_type_id'))
        solution = get_solution(kwargs.get('object_id'), kwargs.get('content_type_id'))

        if solution.settings is None:
            solution.settings = PlateSolvingSettings.objects.create()
            solution.save()

        if solution.submission_id is None:
            solver = Solver()

            try:
                url = target.thumbnail('hd', {
                    'sync': True,
                    'revision_label': '0' if target._meta.model_name == u'image' else target.label
                })

                if solution.settings.blind:
                    submission = solver.solve(url)
                else:
                    submission = solver.solve(
                        url,
                        scale_units=solution.settings.scale_units,
                        scale_lower=solution.settings.scale_min,
                        scale_upper=solution.settings.scale_max,
                        center_ra=solution.settings.center_ra,
                        center_dec=solution.settings.center_dec,
                        radius=solution.settings.radius,
                    )
                solution.status = Solver.PENDING
                solution.submission_id = submission
                solution.save()
            except Exception, e:
                log.error(e)
                solution.status = Solver.MISSING
                solution.submission_id = None
                solution.save()

        context = {
            'solution': solution.id,
            'submission': solution.submission_id,
            'status': solution.status,
        }
        return HttpResponse(simplejson.dumps(context), content_type='application/json')


class SolveAdvancedView(base.View):
    def post(self, request, *args, **kwargs):
        target = get_target(kwargs.get('object_id'), kwargs.get('content_type_id'))
        solution = get_solution(kwargs.get('object_id'), kwargs.get('content_type_id'))

        if solution.advanced_settings is None:
            latest_settings = None

            if target._meta.model_name == u'image':
                images = target._meta.model.objects.filter(user=target.user).order_by('-pk')
                for image in images:
                    if image.solution and image.solution.advanced_settings:
                        latest_settings = image.solution.advanced_settings
                        break
            elif target.image.solution and target.image.solution.advanced_settings:
                    latest_settings = target.image.solution.advanced_settings

            if latest_settings is not None:
                latest_settings.pk = None
                latest_settings.save()
            else:
                latest_settings = PlateSolvingAdvancedSettings.objects.create()

            solution.advanced_settings = latest_settings
            solution.save()

        if solution.pixinsight_serial_number is None or solution.status == SolverBase.SUCCESS:
            solver = AdvancedSolver()

            try:
                observation_time = None
                latitude = None
                longitude = None
                altitude = None

                if solution.advanced_settings.sample_raw_frame_file:
                    url = solution.advanced_settings.sample_raw_frame_file.url
                else:
                    url = target.thumbnail('hd', {
                        'sync': True,
                        'revision_label': '0' if target._meta.model_name == u'image' else target.label
                    })

                if target._meta.model_name == u'image':
                    image = target
                else:
                    image = target.image

                acquisitions = DeepSky_Acquisition.objects.filter(image=image)
                if acquisitions.count() > 0 and acquisitions[0].date:
                    observation_time = acquisitions[0].date.isoformat()

                locations = image.locations.all()
                if locations.count() > 0:
                    location = locations[0]  # Type: Location
                    latitude = degrees_minutes_seconds_to_decimal_degrees(
                        location.lat_deg, location.lat_min, location.lat_sec, location.lat_side
                    )
                    longitude = degrees_minutes_seconds_to_decimal_degrees(
                        location.lon_deg, location.lon_min, location.lon_sec, location.lon_side
                    )
                    altitude = location.altitude

                submission = solver.solve(
                    url,
                    ra=solution.ra,
                    dec=solution.dec,
                    pixscale=solution.pixscale,
                    observation_time=observation_time,
                    latitude=latitude,
                    longitude=longitude,
                    altitude=altitude,
                    advanced_settings=solution.advanced_settings,
                    image_width=target.w,
                    image_height=target.h)

                solution.status = Solver.ADVANCED_PENDING
                solution.pixinsight_serial_number = submission
                solution.save()
            except Exception as e:
                log.error("Error during advanced plate-solving: %s" % e.message)
                solution.status = Solver.MISSING
                solution.submission_id = None
                solution.save()

        context = {
            'solution': solution.id,
            'submission': solution.pixinsight_serial_number,
            'status': solution.status,
        }
        return HttpResponse(simplejson.dumps(context), content_type='application/json')


class SolutionUpdateView(base.View):
    def post(self, request, *args, **kwargs):
        solution = get_object_or_404(Solution, pk=kwargs.pop('pk'))
        solver = None
        status = None

        if solution.status < SolverBase.ADVANCED_PENDING:
            solver = Solver()
            status = solver.status(solution.submission_id)
        else:
            status = solution.status

        if status == Solver.MISSING:
            solution.status = status
            solution.save()

        context = {'status': status}
        return HttpResponse(simplejson.dumps(context), content_type='application/json')


class SolutionFinalizeView(CsrfExemptMixin, base.View):
    def post(self, request, *args, **kwargs):
        solution = get_object_or_404(Solution, pk=kwargs.pop('pk'))
        solver = Solver()
        status = solver.status(solution.submission_id)

        if status == Solver.SUCCESS:
            info = solver.info(solution.submission_id)

            solution.objects_in_field = ', '.join(info['objects_in_field'])

            solution.ra = "%.3f" % info['calibration']['ra']
            solution.dec = "%.3f" % info['calibration']['dec']
            solution.orientation = "%.3f" % info['calibration']['orientation']
            solution.radius = "%.3f" % info['calibration']['radius']
            solution.pixscale = "%.3f" % corrected_pixscale(solution, info['calibration']['pixscale'])

            try:
                target = solution.content_type.get_object_for_this_type(pk=solution.object_id)
            except solution.content_type.model_class().DoesNotExist:
                # Target image was deleted meanwhile
                context = {'status': Solver.FAILED}
                return HttpResponse(simplejson.dumps(context), content_type='application/json')

            # Annotate image
            annotations_obj = solver.annotations(solution.submission_id)
            solution.annotations = simplejson.dumps(annotations_obj)
            annotator = Annotator(solution)

            try:
                annotated_image = annotator.annotate()
            except ThumbnailNotReadyException:
                log.debug("Solution annotation %d: thumbnail not ready" % solution.id)
                solution.status = Solver.PENDING
                solution.save()
                context = {'status': solution.status}
                return HttpResponse(simplejson.dumps(context), content_type='application/json')

            filename, ext = os.path.splitext(target.image_file.name)
            annotated_filename = "%s-%d%s" % (filename, int(time.time()), ext)
            if annotated_image:
                solution.image_file.save(annotated_filename, annotated_image)

            # Get sky plot image
            url = solver.sky_plot_zoom1_image_url(solution.submission_id)
            if url:
                img = NamedTemporaryFile(delete=True)
                img.write(urllib2.urlopen(url).read())
                img.flush()
                img.seek(0)
                f = File(img)
                try:
                    solution.skyplot_zoom1.save(target.image_file.name, f)
                except IntegrityError:
                    pass

        solution.status = status
        solution.save()

        context = {'status': solution.status}
        return HttpResponse(simplejson.dumps(context), content_type='application/json')


class SolutionFinalizeAdvancedView(base.View):
    def post(self, request, *args, **kwargs):
        solution = get_object_or_404(Solution, pk=kwargs.pop('pk'))
        context = {'status': solution.status}
        return HttpResponse(simplejson.dumps(context), content_type='application/json')


class SolutionPixInsightNextTask(base.View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SolutionPixInsightNextTask, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        username = request.POST.get('userName')
        password = request.POST.get('userPassword')

        if username != settings.PIXINSIGHT_USERNAME or password != settings.PIXINSIGHT_PASSWORD:
            return HttpResponseForbidden()

        task = PlateSolvingAdvancedTask.objects.filter(active=True).order_by('-created').first()

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

        log.debug("PixInsight next-task: sending response\n%s" % response)

        return HttpResponse(response)


class SolutionPixInsightWebhook(base.View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SolutionPixInsightWebhook, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        serial_number = request.POST.get('serialNumber')
        status = request.POST.get('status', 'ERROR')

        log.debug("PixInsight Webhook called for %s: %s" % (serial_number, status))

        solution = get_object_or_404(Solution, pixinsight_serial_number=serial_number)

        if status == 'OK':
            svg_hd = request.POST.get('svgAnnotation', None)
            svg_regular = request.POST.get('svgAnnotationSmall', svg_hd)

            solution.pixinsight_svg_annotation_hd.save(serial_number + ".svg", ContentFile(svg_hd))
            solution.pixinsight_svg_annotation_regular.save(serial_number + ".svg", ContentFile(svg_regular))
            solution.status = Solver.ADVANCED_SUCCESS

            solution.advanced_ra = request.POST.get('centerRA', None)
            solution.advanced_ra_top_left = request.POST.get('topLeftRA', None)
            solution.advanced_ra_top_right = request.POST.get('topRightRA', None)
            solution.advanced_ra_bottom_left = request.POST.get('bottomLeftRA', None)
            solution.advanced_ra_bottom_right = request.POST.get('bottomRightRA', None)

            solution.advanced_dec = request.POST.get('centerDec', None)
            solution.advanced_dec_top_left = request.POST.get('topLeftDec', None)
            solution.advanced_dec_top_right = request.POST.get('topRightDec', None)
            solution.advanced_dec_bottom_left = request.POST.get('bottomLeftDec', None)
            solution.advanced_dec_bottom_right = request.POST.get('bottomRightDec', None)

            solution.advanced_orientation = request.POST.get('rotation', None)
            solution.advanced_pixscale = corrected_pixscale(solution, request.POST.get('resolution', None))
            solution.advanced_flipped = request.POST.get('flipped', None) == 'true'
            solution.advanced_wcs_transformation = request.POST.get('wcs_transformation', None)

            solution.advanced_matrix_rect = request.POST.get('matrixRect', None)
            solution.advanced_matrix_delta = request.POST.get('matrixDelta', None)
            solution.advanced_ra_matrix = request.POST.get('raMatrix', None)
            solution.advanced_dec_matrix = request.POST.get('decMatrix', None)

            solution.advanced_annotations = request.POST.get('labelInfo', None)
            solution.advanced_annotations_regular = request.POST.get('labelInfoSmall', None)
        else:
            solution.status = Solver.ADVANCED_FAILED
            log.error(request.POST.get('errorMessage', 'Unknown error'))

        solution.save()

        return HttpResponse("OK")


###############################################################################
# API                                                                         #
###############################################################################


class SolutionList(generics.ListCreateAPIView):
    model = Solution
    queryset = Solution.objects.order_by('pk')
    serializer_class = SolutionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('content_type', 'object_id',)
    filter_class = ImageObjectIdFilter
    pagination_class = None


class SolutionDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Solution
    serializer_class = SolutionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = Solution.objects.all()
