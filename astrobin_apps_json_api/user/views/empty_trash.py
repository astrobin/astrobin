from braces.views import JsonRequestResponseMixin, LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views import View

from astrobin_apps_users.services import UserService


class EmptyTrash(JsonRequestResponseMixin, LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        count = UserService(request.user).empty_trash()
        messages.success(request, _("%(number)s image(s) deleted from your trash." % {"number": count}))
        return self.render_json_response({"status": "OK"})
