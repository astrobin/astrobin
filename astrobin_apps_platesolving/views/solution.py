import os
import time
import urllib2

import simplejson
from braces.views import CsrfExemptMixin
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import base
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework import permissions

from astrobin_apps_platesolving.annotate import Annotator
from astrobin_apps_platesolving.api_filters.image_object_id_filter import ImageObjectIdFilter
from astrobin_apps_platesolving.models import PlateSolvingSettings
from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.serializers import SolutionSerializer
from astrobin_apps_platesolving.solver import Solver
from astrobin_apps_platesolving.utils import getFromStorage


class SolveView(base.View):
    def post(self, request, *args, **kwargs):
        object_id = kwargs.pop('object_id')
        content_type_id = kwargs.pop('content_type_id')

        content_type = ContentType.objects.get_for_id(content_type_id)
        manager = content_type.model_class()
        if hasattr(manager, 'objects_including_wip'):
            manager = manager.objects_including_wip
        target = get_object_or_404(manager, pk=object_id)
        solution, created = Solution.objects.get_or_create(object_id=object_id, content_type=content_type)
        if solution.settings is None:
            solution.settings = PlateSolvingSettings.objects.create()
            solution.save()

        if solution.submission_id is None:
            solver = Solver()

            try:
                f = getFromStorage(target, 'hd', '0' if content_type.model == 'image' else target.label)

                if solution.settings.blind:
                    submission = solver.solve(f)
                else:
                    submission = solver.solve(f,
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
            except:
                solution.status = Solver.MISSING
                solution.submission_id = None
                solution.save()

        context = {
            'solution': solution.id,
            'submission': solution.submission_id,
            'status': solution.status,
        }
        return HttpResponse(simplejson.dumps(context), content_type='application/json')


class SolutionUpdateView(base.View):
    def post(self, request, *args, **kwargs):
        solution = get_object_or_404(Solution, pk=kwargs.pop('pk'))
        solver = Solver()
        status = solver.status(solution.submission_id)

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

            # Get the images 'w' and adjust pixscale
            if solution.content_object:
                w = solution.content_object.w
                pixscale = info['calibration']['pixscale']
                if w and pixscale:
                    hd_w = settings.THUMBNAIL_ALIASES['']['hd']['size'][0]
                    if hd_w > w:
                        hd_w = w
                    ratio = hd_w / float(w)
                    corrected_scale = float(pixscale) * ratio
                    solution.pixscale = "%.3f" % corrected_scale
                else:
                    solution.pixscale = None

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
            annotated_image = annotator.annotate()
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


class SolutionDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Solution
    serializer_class = SolutionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    queryset = Solution.objects.all()
