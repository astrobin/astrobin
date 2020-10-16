from braces.views import JsonRequestResponseMixin, LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views import View

from astrobin.models import Image
from astrobin_apps_images.services import ImageService


class ConfirmImageRecovery(JsonRequestResponseMixin, LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pks = self.request_json["images"]

        if len(pks) > 0:
            images = Image.all_objects.filter(corrupted=True, user=request.user, pk__in=pks).exclude(recovered=None)

            if len(pks) != images.count():
                return self.render_bad_request_response()

            for image in images.iterator():
                ImageService(image) \
                        .get_revisions(include_corrupted=True, include_deleted=True) \
                        .exclude(recovered=None) \
                        .update(corrupted=False)

            images.update(corrupted=False)

            messages.success(request, _("%(number)s image(s) recovered." % {"number": len(pks)}))

        return self.render_json_response({u"status": u"OK"})
