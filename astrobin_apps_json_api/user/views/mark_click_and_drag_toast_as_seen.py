from datetime import datetime, timedelta

from braces.views import JsonRequestResponseMixin
from django.views import View


class MarkClickAndDragToastAsSeen(JsonRequestResponseMixin, View):
    def post(self, request, *args, **kwargs):
        response = self.render_json_response({u"status": u"OK"})
        max_age = 365 * 10 * 24 * 60 * 60
        expires = datetime.strftime(datetime.utcnow() + timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
        response.set_cookie("astrobin_click_and_drag_toast_seen", 1, max_age=max_age, expires=expires)

        return response
