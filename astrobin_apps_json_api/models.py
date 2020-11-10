from __future__ import absolute_import

from django.contrib.auth.models import User
from django.db import models
from safedelete.models import SafeDeleteModel

from common.upload_paths import upload_path


def ckeditor_upload_path(instance, filename):
    return upload_path('ckeditor-files', instance.user.pk, filename)

class CkEditorFile(SafeDeleteModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    uploaded = models.DateTimeField(auto_now_add=True, null=False, blank=True)

    upload = models.FileField(
        upload_to=ckeditor_upload_path,
        max_length=1024,
        null=False,
    )

    filename = models.CharField(max_length=256)

    filesize = models.PositiveIntegerField()
