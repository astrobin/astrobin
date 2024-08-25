import logging
import os
from io import BytesIO

from braces.views import CsrfExemptMixin, JSONResponseMixin, LoginRequiredMixin
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View
from easy_thumbnails.files import get_thumbnailer

from astrobin_apps_json_api.common.forms.CkEditorUploadForm import CkEditorUploadForm
from astrobin_apps_json_api.models import CkEditorFile
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import (
    is_any_lite, is_any_premium,
    is_any_ultimate,
)

log = logging.getLogger(__name__)


class CkEditorUpload(CsrfExemptMixin, JSONResponseMixin, View):
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

    def get(self, request, *args, **kwargs):
        path = request.GET.get('path', None)

        if path is None:
            raise Http404

        upload = get_object_or_404(CkEditorFile, upload=path)

        return self.render_json_response(
            {
                "pk": upload.pk,
                "fileName": upload.filename,
                "url": upload.upload.url,
                "thumbnail": upload.thumbnail.url if upload.thumbnail else None,
            }
        )

    def post(self, request, *args, **kwargs):
        log.info("CkEditorUpload: user %d - requested file upload" % request.user.pk)

        if settings.READONLY_MODE:
            return self.upload_error(
                request,
                _("AstroBin is currently in read-only mode, because of server maintenance. Please try again soon!"))

        if not request.user.is_authenticated:
            return self.upload_error(request, _("You must be logged in to upload files"))

        MB = 1024 * 1024

        valid_subscription = PremiumService(request.user).get_valid_usersubscription()

        if is_any_lite(valid_subscription):
            max_size = MB * 5
        elif is_any_premium(valid_subscription):
            max_size = MB * 10
        elif is_any_ultimate(valid_subscription):
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

        if self.is_image(uploaded_file):
            try:
                self.create_and_save_thumbnail(upload)
            except Exception as e:
                log.error("CkEditorUpload: user %d - error while creating thumbnail: %s" % (request.user.pk, e))

        return self.render_json_response({
            "uploaded": 1,
            "fileName": upload.filename,
            "url": upload.upload.url,
            "thumbnail": upload.thumbnail.url if upload.thumbnail else None,
        })

    def is_image(self, uploaded_file) -> bool:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        return file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']

    def create_and_save_thumbnail(self, upload):
        options = {
            'size': (1024, 0),
            'crop': True,
            'keep_icc_profile': True,
            'quality': 80,
        }

        thumbnailer = get_thumbnailer(upload.upload)
        thumbnail = thumbnailer.get_thumbnail(options)

        thumb_io = BytesIO()
        with thumbnail.open('rb') as thumb_file:
            thumb_io.write(thumb_file.read())
            thumb_io.seek(0)

        upload.thumbnail.save(thumbnail.name, ContentFile(thumb_io.read()))

        thumb_io.close()
