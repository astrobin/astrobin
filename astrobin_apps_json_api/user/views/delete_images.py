from annoying.functions import get_object_or_None
from braces.views import JsonRequestResponseMixin, LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views import View

from astrobin.models import Image


class DeleteImages(JsonRequestResponseMixin, LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pks = self.request_json["images"]

        if len(pks) > 0:
            for pk in pks:
                image: Image = get_object_or_None(Image.all_objects, pk=pk)
                if image is None or image.user != request.user:
                    return self.render_bad_request_response()

                image.delete()

            messages.success(request, _("%(number)s image(s) deleted." % {"number": len(pks)}))

        return self.render_json_response({"status": "OK"})
