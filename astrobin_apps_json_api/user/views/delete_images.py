from braces.views import JsonRequestResponseMixin, LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views import View

from astrobin.models import Image


class DeleteImages(JsonRequestResponseMixin, LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pks = self.request_json["images"]

        if len(pks) > 0:
            images = Image.all_objects.filter(user=request.user, pk__in=pks)

            if len(pks) != images.count():
                return self.render_bad_request_response()

            for image in images:
                if image.corrupted and image.recovered:
                    image.corrupted = False
                    image.save(keep_deleted=True)

            images.delete()

            messages.success(request, _("%(number)s image(s) deleted." % {"number": len(pks)}))

        return self.render_json_response({u"status": u"OK"})
