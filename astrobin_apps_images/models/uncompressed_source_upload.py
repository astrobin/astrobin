from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from astrobin.models import Image
from common.upload_paths import uncompressed_source_upload_path
from common.validators import FileValidator


class UncompressedSourceUpload(models.Model):
    image = models.ForeignKey(
        Image,
        related_name="uncompressed_source_upload")

    uncompressed_source_file = models.FileField(
        upload_to=uncompressed_source_upload_path,
        validators=(FileValidator(allowed_extensions=settings.ALLOWED_UNCOMPRESSED_SOURCE_EXTENSIONS),),
        verbose_name=_("Uncompressed source (max 100 MB)"),
        help_text=_(
            "You can store the final processed image that came out of your favorite image editor (e.g. PixInsight, "
            "Adobe Photoshop, etc) here on AstroBin, for archival purposes. This file is stored privately and only you "
            "will have access to it."),
        max_length=256,
        null=True,
    )

    uploader_name = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        editable=False,
    )

    uploader_upload_length = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=False,
    )

    uploader_offset = models.PositiveIntegerField(
        null=True,
        blank=True,
        editable=False,
    )

    uploader_expires = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
    )

    uploader_metadata = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        editable=False,
    )

    uploader_temporary_file_path = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        editable=False,
    )

    def __unicode__(self):
        return u"UncompressedSourceUpload for image %s: %s" % (self.image.pk, self.uncompressed_source_file)

    class Meta:
        app_label = "astrobin_apps_images"
