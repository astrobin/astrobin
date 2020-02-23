from braces.views import JsonRequestResponseMixin, LoginRequiredMixin
from django.views import View


class MarkCorruptedImagesBannerAsSeen(JsonRequestResponseMixin, LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        response = self.render_json_response({u"status": u"OK"})
        response.set_cookie("astrobin_corrupted_images_banner_seen", 1)

        return response
