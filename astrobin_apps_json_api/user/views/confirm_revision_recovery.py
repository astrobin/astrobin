from braces.views import JsonRequestResponseMixin, LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views import View

from astrobin.models import Image, ImageRevision


class ConfirmRevisionRecovery(JsonRequestResponseMixin, LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pks = self.request_json["revisions"]

        if len(pks) > 0:
            revisions = ImageRevision.all_objects.filter(corrupted=True, image__user=request.user, pk__in=pks).exclude(recovered=None)

            if len(pks) != revisions.count():
                return self.render_bad_request_response()

            revisions.update(corrupted=False)

            messages.success(request, _("%(number)s revisions(s) recovered." % {"number": len(pks)}))

        return self.render_json_response({u"status": u"OK"})
