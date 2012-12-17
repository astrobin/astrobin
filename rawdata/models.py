# Python
import os
import uuid

# Django
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import m2m_changed
from django.utils.translation import ugettext_lazy as _

# This app
from .managers import RawImageManager, SoftDeleteManager

# Other AstroBin apps
from astrobin.models import Image


def upload_path(instance, filename):
    instance.original_filename = filename
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('rawdata', str(instance.user.id), filename)

def temporary_download_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.zip" % uuid.uuid4()
    return os.path.join('tmpzips', filename)


class RawImage(models.Model):
    objects = RawImageManager()

    # Definitions
    TYPE_UNKNOWN = 0
    TYPE_LIGHT   = 1
    TYPE_OFFSET  = 2 
    TYPE_DARK    = 3
    TYPE_FLAT    = 4

    TYPE_CHOICES = (
        (TYPE_UNKNOWN, _('Unknown')),
        (TYPE_LIGHT,   _('Light')),
        (TYPE_OFFSET,  _('Offset/Bias')),
        (TYPE_DARK,    _('Dark')),
        (TYPE_FLAT,    _('Flat')),
    )

    user = models.ForeignKey(
        User,
        editable = False
    )

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

    acquisition_date = models.DateTimeField(
        null = True,
        blank = True,
        editable = False,
    )

    camera = models.CharField(
        max_length = 128,
        null = True,
        blank = True,
        editable = False,
    )

    temperature = models.SmallIntegerField(
        null = True,
        blank = True,
        editable = False,
    )

    class Meta:
        app_label = 'rawdata'
        ordering = ('-uploaded',)

    def __unicode__(self):
        return self.original_filename

    def save(self, *args, **kwargs):
        index = kwargs.pop('index', False)
        super(RawImage, self).save(*args, **kwargs)
        if index:
            from .tasks import index_raw_image
            index_raw_image.delay(self.id)

    def delete(self):
        self.active = False
        self.save()


class TemporaryArchive(models.Model):
    objects = SoftDeleteManager()

    user = models.ForeignKey(
        User,
        editable = False,
    )

    file = models.FileField(
        storage = FileSystemStorage(location = '/webserver/www'),
        upload_to = temporary_download_upload_path,
    )

    size = models.IntegerField(
        default = 0,
        editable = False,
    )

    created = models.DateTimeField(
        auto_now_add = True,
        editable = False,
    )

    active = models.BooleanField(
        default = True,
        editable = False,
    )

    class Meta:
        app_label = 'rawdata'

    def __unicode__(self):
        return self.file.name

    def delete(self):
        self.active = False
        self.save()


class PublicDataPool(models.Model):
    objects = SoftDeleteManager()

    name = models.CharField(
        max_length = 128,
        unique = True,
        verbose_name = _("Name"),
        help_text = _("A public name for this pool. Be descriptive, include the name of the celestial object and a target focal length in millimeters."),
    )

    description = models.TextField(
        verbose_name = _("Description"),
        help_text = _("Describe the goals and terms of this pool."),
    )

    creator = models.ForeignKey(
        User,
        editable = False,
        on_delete = models.SET_NULL,
        null = True,
    )

    created = models.DateTimeField(
        auto_now_add = True,
        editable = False,
    )

    updated = models.DateTimeField(
        auto_now = True,
        editable = False,
    )

    images = models.ManyToManyField(
        RawImage,
        null = True,
    )

    processed_images = models.ManyToManyField(
        Image,
        null = True,
    )

    archive = models.ForeignKey(
        TemporaryArchive,
        null = True,
        on_delete = models.SET_NULL,
        editable = False,
    )

    active = models.BooleanField(
        default = True,
        editable = False,
    )

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'rawdata'
        ordering = ('-updated',)

    def delete(self):
        self.active = False
        self.save()

    def get_absolute_url(self):
        return reverse('rawdata.publicdatapool_detail', args=(self.pk,))


class PrivateSharedFolder(models.Model):
    objects = SoftDeleteManager()

    name = models.CharField(
        max_length = 128,
        verbose_name = _("Name"),
        help_text = _("A name for this folder. Be descriptive, so that the folder can be quickly recognized by the name."),
    )

    description = models.TextField(
        verbose_name = _("Description"),
        help_text = _("Describe the goals of this folder."),
    )

    creator = models.ForeignKey(
        User,
        editable = False,
        related_name = 'privatesharedfolders_created',
    )

    created = models.DateTimeField(
        auto_now_add = True,
        editable = False,
    )

    updated = models.DateTimeField(
        auto_now = True,
        editable = False,
    )

    users = models.ManyToManyField(
        User,
        related_name = 'privatesharedfolders_invited',
    )

    images = models.ManyToManyField(
        RawImage,
        null = True,
        blank = True,
    )

    processed_images = models.ManyToManyField(
        Image,
        null = True,
        blank = True,
    )

    archive = models.ForeignKey(
        TemporaryArchive,
        null = True,
        on_delete = models.SET_NULL,
        editable = False,
    )

    active = models.BooleanField(
        default = True,
        editable = False,
    )

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'rawdata'
        ordering = ('-updated',)

    def delete(self):
        self.active = False
        self.save()

    def get_absolute_url(self):
        return reverse('rawdata.publicdatapool_detail', args=(self.pk,))


def on_images_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    instance.archive = None
    instance.save()

m2m_changed.connect(on_images_changed, sender = PublicDataPool.images.through)
m2m_changed.connect(on_images_changed, sender = PrivateSharedFolder.images.through)

