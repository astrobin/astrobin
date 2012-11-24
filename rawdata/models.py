# Python
import os
import uuid

# Django
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.utils.translation import ugettext_lazy as _

# This app
from .managers import SoftDeleteManager

def upload_path(instance, filename):
    instance.original_filename = filename
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('rawdata', str(instance.user.id), filename)


class RawImage(models.Model):
    objects = SoftDeleteManager()

    # Definitions
    TYPE_UNKNOWN = 0
    TYPE_OFFSET  = 10
    TYPE_DARK    = 20
    TYPE_FLAT    = 30
    TYPE_LIGHT   = 40

    TYPE_CHOICES = (
        (TYPE_UNKNOWN, _('Unknown')),
        (TYPE_OFFSET,  _('Offset/Bias')),
        (TYPE_DARK,    _('Dark')),
        (TYPE_FLAT,    _('Flat')),
        (TYPE_LIGHT,   _('Light')),
    )

    user = models.ForeignKey(
        User,
        editable = False)

    file = models.FileField(
        storage = FileSystemStorage(location = '/webserver/www'),
        upload_to = upload_path,
    )

    original_filename = models.CharField(
        max_length = 256,
        editable = False,
    )

    size = models.IntegerField(
        default = 0,
        editable = False,
    )

    uploaded = models.DateTimeField(
        auto_now_add = True,
        editable = False,
    )

    indexed = models.BooleanField(
        default = False,
        editable = False,
    )

    active = models.BooleanField(
        default = True,
        editable = False,
    )

    image_type = models.IntegerField(
        max_length = 1,
        default = 0, # Unknown
        choices = TYPE_CHOICES,
        editable = False,
    )

    class Meta:
        app_label = 'rawdata'

    def __unicode__(self):
        return self.original_filename

    def save(self, *args, **kwargs):
        index = kwargs.pop('index', True)
        super(RawImage, self).save(*args, **kwargs)
        if index:
            from .tasks import index_raw_image
            index_raw_image.delay(self.id)

    def delete(self, *args, **kwargs):
        self.active = False
        self.save(index = False)
