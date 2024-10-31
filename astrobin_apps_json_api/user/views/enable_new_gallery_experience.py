from braces.views import JsonRequestResponseMixin
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from astrobin.models import UserProfile


@method_decorator(csrf_exempt, name='dispatch')
class EnableNewGalleryExperience(JsonRequestResponseMixin, View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        profile: UserProfile = request.user.userprofile

        if not profile.may_enable_new_gallery_experience:
            return HttpResponseBadRequest()

        profile.enable_new_gallery_experience = True
        profile.save()

        return self.render_json_response({"status": "OK"})
