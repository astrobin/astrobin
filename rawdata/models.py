# Python
import os
import uuid

# Django
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.db import models

def upload_path(instance, filename):
    instance.original_filename = filename
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('rawdata', str(instance.user.id), filename)


class RawImage(models.Model):
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

    image_type = models.CharField(
        max_length = 1,
        default = 'U', # Unknown
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

