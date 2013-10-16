# Python
import simplejson

# Django
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import base

# restframework
from rest_framework import generics
from rest_framework import permissions

# AstroBin apps
from astrobin.models import Image # TODO: model will be moved to astrobin_apps_images
from common.mixins import AjaxableResponseMixin

# This app
from astrobin_apps_platesolving.models import Solution
from astrobin_apps_platesolving.serializers import SolutionSerializer
from astrobin_apps_platesolving.solver import Solver


class SolveView(base.View):
    def post(self, request, *args, **kwargs):
        image = get_object_or_404(Image, pk = kwargs.pop('pk'))
        solution = image.solution

        if solution is None:
            solution = Solution()
            solution.save()

            image.solution = solution
            image.save()

        if solution.submission_id is None:
            solver = Solver()
            submission = solver.solve(image.image_file)
            solution.status = Solver.PENDING
            solution.submission_id = submission
            solution.save()

        context = {'submission': solution.submission_id}
        return HttpResponse(simplejson.dumps(context), mimetype='application/json')


class SolutionUpdateView(base.View):
    def post(self, request, *args, **kwargs):
        solution = get_object_or_404(Solution, pk = kwargs.pop('pk'))
        solver = Solver()
        solution.status = solver.status(solution.submission_id)
        solution.save()

        context = {'status': solution.status}
        return HttpResponse(simplejson.dumps(context), mimetype='application/json')


###############################################################################
# API                                                                         #
###############################################################################


class SolutionList(generics.ListCreateAPIView):
    model = Solution
    queryset = Solution.objects.order_by('pk')
    serializer_class = SolutionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class SolutionDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Solution
    serializer_class = SolutionSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

