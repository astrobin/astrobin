from annoying.functions import get_object_or_None
from braces.views import JsonRequestResponseMixin, LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views import View

from astrobin.models import ImageRevision


class DeleteRevisions(JsonRequestResponseMixin, LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pks = self.request_json["revisions"]

        if len(pks) > 0:
            for pk in pks:
                revision: ImageRevision = get_object_or_None(ImageRevision.all_objects, pk=pk)
                if revision is None or revision.image.user != request.user:
                    return self.render_bad_request_response()

                revision.delete()

            messages.success(request, _("%(number)s revisions(s) deleted." % {"number": len(pks)}))

        return self.render_json_response({"status": "OK"})
