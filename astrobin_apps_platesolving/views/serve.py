import os

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import View

from astrobin.services.utils_service import UtilsService
from astrobin_apps_platesolving.models import Solution


class ServeAdvancedSvg(View):
    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.pop('pk')
        self.resolution = kwargs.pop('resolution', 'regular')  # type: str
        self.solution = get_object_or_404(Solution, pk=pk)  # type: Solution

        return super(ServeAdvancedSvg, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.resolution == 'hd':
            image_file = self.solution.pixinsight_svg_annotation_hd
        else:
            image_file = self.solution.pixinsight_svg_annotation_regular

        if image_file != '':
            response = UtilsService.http_with_retries(image_file.url, headers={'User-Agent': 'Mozilla/5.0'})
            ret = HttpResponse(response.content, content_type="image/svg+xml")
            ret['Content-Disposition'] = 'inline; filename=' + os.path.basename(image_file.name)
            return ret

        return HttpResponse(status=404)

