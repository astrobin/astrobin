import uuid
from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django import forms

def upload_image_to(instance, filename):
    format = 'images/%Y/%m/%d'
    prefix = os.path.normpath(force_unicode(datetime.datetime.now().strftime(smart_str(format))))
    postfix = '%s%s' % (
            string.join(random.sample(string.ascii_letters + string.digits, 5), ''),
            os.path.splitext(filename)[-1],
            )
    filepath = '%s_%s' % (prefix, postfix)
    return filepath

class Gear(models.Model):
    name = models.CharField(max_length=64)
    purchase_date = models.DateTimeField('date purchased')

    def __unicode__(self):
        return self.name

class Camera(Gear):
    chip_size = models.IntegerField()

class Telescope(Gear):
    focal_length = models.IntegerField()
    aperture = models.IntegerField()

class Mount(Gear):
    pass

class FocalReducer(Gear):
    ratio = models.DecimalField(max_digits=3, decimal_places=2)

class Subject(models.Model):
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name

class Image(models.Model):
    subjects = models.CharField(max_length=128)
    url = models.CharField(max_length=128)
    uploaded = models.DateTimeField()

    # gear
    camera = models.CharField(max_length=32)
    focal_reducer = models.CharField(max_length=32)
    telescope = models.CharField(max_length=32)
    mount = models.CharField(max_length=32)

    description = models.TextField()

    def __unicode__(self):
        return self.subjects

    def save(self):
        self.uploaded = datetime.now()
        models.Model.save(self)
