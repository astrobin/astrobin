import logging

from braces.views import JSONResponseMixin, LoginRequiredMixin, CsrfExemptMixin
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View

from astrobin_apps_json_api.common.forms.CkEditorUploadForm import CkEditorUploadForm
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_any_lite, is_any_premium, \
    is_any_ultimate

log = logging.getLogger("apps")


class CkEditorUpload(CsrfExemptMixin, LoginRequiredMixin, JSONResponseMixin, View):
    def upload_error(self, request, message=None):
        if message is None:
            message = _("File upload failed. An unexpected error occurred")

        log.error("CkEditorUpload: user %d - %s" % (request.user.pk, message))

        return self.render_json_response({
            "uploaded": 0,
            "error": {
                "message": message
            }
        })

    def post(self, request, *args, **kwargs):
        log.info("CkEditorUpload: user %d - requested file upload" % request.user.pk)

        if settings.READONLY_MODE:
            return self.upload_error(
                request,
                _("AstroBin is currently in read-only mode, because of server maintenance. Please try again soon!"))

        MB = 1024 * 1024

        if is_any_lite(request.user):
            max_size = MB * 5
        elif is_any_premium(request.user):
            max_size = MB * 10
        elif is_any_ultimate(request.user):
            max_size = MB * 20
        else:
            max_size = MB * 1

        form = CkEditorUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            return self.upload_error(request)

        uploaded_file = request.FILES['upload']
        if uploaded_file.size > max_size:
            return self.upload_error(
                request, _("The file is too large. Maximum size: %d MB." % (max_size / MB)))

        upload = form.save(commit=False)
        upload.user = request.user
        upload.filename = uploaded_file.name
        upload.filesize = uploaded_file.size
        upload.save(keep_deleted=True)

        return self.render_json_response({
            "uploaded": 1,
            "fileName": upload.filename,
            "url": upload.upload.url,
        })
