from braces.views import JsonRequestResponseMixin, LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views import View

from astrobin.models import Image, ImageRevision


class DeleteRevisions(JsonRequestResponseMixin, LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pks = self.request_json["revisions"]

        if len(pks) > 0:
            revisions = ImageRevision.objects.filter(image__user=request.user, pk__in=pks)

            if len(pks) != revisions.count():
                return self.render_bad_request_response()

            revisions.delete()

            messages.success(request, _("%(number)s revisions(s) deleted." % {"number": len(pks)}))

        return self.render_json_response({u"status": u"OK"})
