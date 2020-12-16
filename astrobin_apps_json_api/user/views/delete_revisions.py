from braces.views import JsonRequestResponseMixin, LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views import View

from astrobin.models import ImageRevision


class DeleteRevisions(JsonRequestResponseMixin, LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pks = self.request_json["revisions"]

        if len(pks) > 0:
            revisions = ImageRevision.all_objects.filter(image__user=request.user, pk__in=pks)

            if len(pks) != revisions.count():
                return self.render_bad_request_response()

            for revision in revisions:
                if revision.corrupted and revision.recovered:
                    revision.corrupted = False
                    revision.save(keep_deleted=True)

            revisions.delete()

            messages.success(request, _("%(number)s revisions(s) deleted." % {"number": len(pks)}))

        return self.render_json_response({u"status": u"OK"})
