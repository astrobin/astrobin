from datetime import datetime

from braces.views import JsonRequestResponseMixin, LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views import View

from astrobin.models import UserProfile


class PlateSolutionOverlayOnFullDisabled(JsonRequestResponseMixin, LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        profile = get_object_or_404(UserProfile, user=request.user)
        status = self.request_json["status"]

        if status:
            profile.plate_solution_overlay_on_full_disabled = None
        else:
            profile.plate_solution_overlay_on_full_disabled = datetime.now()

        profile.save(keep_deleted=True)

        response = self.render_json_response({
            u"plate_solution_overlay_on_full_disabled": profile.plate_solution_overlay_on_full_disabled
        })

        return response
