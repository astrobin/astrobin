from datetime import datetime, timedelta

from braces.views import JsonRequestResponseMixin, LoginRequiredMixin
from django.views import View


class MarkCorruptedImagesBannerAsSeen(JsonRequestResponseMixin, LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        response = self.render_json_response({u"status": u"OK"})
        max_age = 365 * 10 * 24 * 60 * 60
        expires = datetime.strftime(datetime.utcnow() + timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
        response.set_cookie("astrobin_corrupted_images_banner_seen", 1, max_age=max_age, expires=expires)

        return response
