from braces.views import JsonRequestResponseMixin, LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views import View

from astrobin.models import Image


class RestoreDeletedImages(JsonRequestResponseMixin, LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pks = self.request_json["images"]
        images = Image.all_objects.filter(user=request.user, pk__in=pks)

        if len(pks) != images.count():
            return self.render_bad_request_response()

        images.undelete()

        messages.success(request, _("%(number)s image(s) restored." % {"number": len(pks)}))
        return self.render_json_response({u"status": u"OK"})
