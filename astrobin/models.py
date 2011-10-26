import uuid
from datetime import datetime
import glob
import os
import urllib2
import simplejson

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django import forms
from django.utils.translation import ugettext as _
from django.conf import settings

from celery.decorators import task

from djangoratings.fields import RatingField
from model_utils.managers import InheritanceManager

from tasks import store_image, solve_image, delete_image
from notifications import push_notification

class Gear(models.Model):
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'astrobin'


class Telescope(Gear):
    focal_length = models.IntegerField(null=True, blank=True)
    aperture = models.IntegerField(null=True, blank=True)

    class Meta:
        app_label = 'astrobin'


class Mount(Gear):
    pass

    class Meta:
        app_label = 'astrobin'


class Camera(Gear):
    pass

    class Meta:
        app_label = 'astrobin'


class FocalReducer(Gear):
    ratio = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)

    class Meta:
        app_label = 'astrobin'


class Software(Gear):
    pass

    class Meta:
        app_label = 'astrobin'


class Filter(Gear):
    pass

    class Meta:
        app_label = 'astrobin'


class Accessory(Gear):
    pass

    class Meta:
        app_label = 'astrobin'


class Subject(models.Model):
    # Simbad object id
    oid = models.IntegerField()
    # Right ascension
    ra = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    # Declination
    dec = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    # Main object identifier (aka main name)
    mainId = models.CharField(max_length=64, unique=True)
    # Object type
    otype = models.CharField(max_length=16, null=True, blank=True)
    # Morphological type
    mtype = models.CharField(max_length=16, null=True, blank=True)
    # Dimensions along the major and minor axis
    dim_majaxis = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    dim_minaxis = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # The list of identifier (aka alternative names) is done via
    # a many-to-one relationship in SubjectIdentifier.

    def __unicode__(self):
        return self.mainId

    class Meta:
        app_label = 'astrobin'

    # Note: this function doesn't deal with the alternative names.
    def initFromJSON(self, json):
        for attr in [field.name for field in self._meta.fields]:
            if attr != 'id' and attr in json:
                setattr(self, attr, json[attr])

    def getFromSimbad(self):
        if not self.mainId:
            return
        url = settings.SIMBAD_SEARCH_URL + self.mainId
        f = None
        try:
            f = urllib2.urlopen(url)
        except:
            return;

        json = simplejson.loads(f.read())
        self.initFromJson(json)
        f.close()


class SubjectIdentifier(models.Model):
    identifier = models.CharField(max_length=64, unique=True)
    subject = models.ForeignKey(Subject, related_name='idlist')

    class Meta:
        app_label = 'astrobin'

    def __unicode__(self):
        return self.identifier


class Location(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    longitude = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    altitude = models.IntegerField(null=True, blank=True)
    user_generated = models.BooleanField()

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'astrobin'


def image_solved_callback(image, solved, clean_path):
    image.is_solved = solved
    if image.__class__ == 'Image' and image.is_solved:
        # grab objects from list
        list_fn = settings.UPLOADS_DIRECTORY + image.filename + '-list.txt'
        f = open(list_fn, 'r')
        for line in f:
            if line != '':
                s, created = Subject.objects.get_or_create(name=line.rstrip('\r\n'))
                if created:
                    s.save()
                image.subjects.add(s)
        f.close()

    image.save()

    # Clean up!
    clean_list = glob.glob(clean_path)
    for f in clean_list:
        os.remove(f)


@task
def image_stored_callback(image, stored, solve):
    image.is_stored = stored
    image.save()

    if solve:
        solve_image.delay(image, callback=image_solved_callback)


class Image(models.Model):
    title = models.CharField(max_length=128)
    subjects = models.ManyToManyField(Subject)
    locations = models.ManyToManyField(Location, null=True, blank=True)
    description = models.TextField()
    filename = models.CharField(max_length=64, editable=False)
    original_ext = models.CharField(max_length=6, editable=False)
    uploaded = models.DateTimeField(editable=False)

    # gear
    imaging_telescopes = models.ManyToManyField(Telescope, null=True, blank=True, related_name='imaging_telescopes')
    guiding_telescopes = models.ManyToManyField(Telescope, null=True, blank=True, related_name='guiding_telescopes')
    mounts = models.ManyToManyField(Mount, null=True, blank=True)
    imaging_cameras = models.ManyToManyField(Camera, null=True, blank=True, related_name='imaging_cameras')
    guiding_cameras = models.ManyToManyField(Camera, null=True, blank=True, related_name='guiding_cameras')
    focal_reducers = models.ManyToManyField(FocalReducer, null=True, blank=True)
    software = models.ManyToManyField(Software, null=True, blank=True)
    filters = models.ManyToManyField(Filter, null=True, blank=True)
    accessories = models.ManyToManyField(Accessory, null=True, blank=True)

    rating = RatingField(range=5)
    user = models.ForeignKey(User)

    is_stored = models.BooleanField(editable=False)
    is_solved = models.BooleanField(editable=False)

    class Meta:
        app_label = 'astrobin'
        ordering = ('-uploaded', '-id')
        
    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.uploaded = datetime.now()
        super(Image, self).save(*args, **kwargs)

        # Find requests and mark as fulfilled
        try:
            req = ImageRequest.objects.filter(
                image = self.id,
                type = 'INFO',
                fulfilled = False)
            for r in req:
                r.fulfilled = True
                r.save()
                push_notification(
                    [r.from_user], 'request_fulfilled',
                    {'object': self,
                     'object_url': settings.ASTROBIN_SHORT_BASE_URL + self.get_absolute_url(),
                     'originator': r.to_user,
                     'originaror_url': r.to_user.get_absolute_url()})
        except:
            pass

    def process(self):
        store_image.delay(self, solve=True, callback=image_stored_callback)

    def delete(self, *args, **kwargs):
        delete_image.delay(self.filename, self.original_ext) 

        # Delete references
        for r in ImageRequest.objects.filter(image=self):
            r.delete()

        super(Image, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        return '/%i' % self.id


class ImageRevision(models.Model):
    image = models.ForeignKey(Image)
    filename = models.CharField(max_length=64, editable=False)
    original_ext = models.CharField(max_length=6, editable=False)
    uploaded = models.DateTimeField(editable=False)

    is_stored = models.BooleanField(editable=False)
    is_solved = models.BooleanField(editable=False)

    class Meta:
        app_label = 'astrobin'
        ordering = ('uploaded', '-id')
        
    def __unicode__(self):
        return 'Revision for %s' % self.image.title

    def save(self, *args, **kwargs):
        self.uploaded = datetime.now()
        super(ImageRevision, self).save(*args, **kwargs)

    def process(self):
        store_image.delay(self, solve=True, callback=image_stored_callback)

    def delete(self, *args, **kwargs):
        delete_image_from_s3(self.filename, self.original_ext) 
        super(ImageRevision, self).delete(*args, **kwargs)

    def get_absolute_url(self):
        return '/%i?r=%i' % (self.image.id, self.id)
 

class Acquisition(models.Model):
    date = models.DateField(null=True, blank=True)
    image = models.ForeignKey(Image)

    class Meta:
        app_label = 'astrobin'

    def __unicode__(self):
        return self.image.title


class DeepSky_Acquisition(Acquisition):
    acquisition_type = models.CharField(max_length=2)
    number = models.IntegerField()
    duration = models.IntegerField(null=True, blank=True)
    iso = models.IntegerField(null=True, blank=True)

    class Meta:
        app_label = 'astrobin'
        ordering = ['acquisition_type']


class SolarSystem_Acquisition(Acquisition):
    frames = models.IntegerField(null=True, blank=True)
    fps = models.IntegerField(null=True, blank=True)
    focal_length = models.IntegerField(null=True, blank=True)
    cmi = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2)
    cmii = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2)
    cmiii = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2)
    seeing = models.IntegerField(null=True, blank=True)
    transparency = models.IntegerField(null=True, blank=True)
    time = models.CharField(null=True, blank=True, max_length=5)

    class Meta:
        app_label = 'astrobin'


class ABPOD(models.Model):
    image = models.ForeignKey(Image, unique=True)
    date = models.DateTimeField()

    def __unicode__(self):
        return self.image.subjects

    class Meta:
        app_label = 'astrobin'


class Request(models.Model):
    from_user = models.ForeignKey(User, editable=False, related_name='requester')
    to_user   = models.ForeignKey(User, editable=False, related_name='requestee')
    fulfilled = models.BooleanField()
    message   = models.CharField(max_length=255)
    created   = models.DateTimeField(auto_now_add=True)

    objects   = InheritanceManager()

    def __unicode__(self):
        return '%s %s: %s' % (_('Request from'), self.from_user.username, self.message)

    class Meta:
        app_label = 'astrobin'
        ordering = ['-created']

    def get_absolute_url():
        return '/requests/detail/' + self.id + '/'


class ImageRequest(Request):
    TYPE_CHOICES = (
        ('INFO',     _('Additional information')),
        ('FITS',     _('TIFF/FITS')),
        ('HIRES',    _('Higher resolution')),
    )

    image = models.ForeignKey(Image, editable=False)
    type  = models.CharField(max_length=8, choices=TYPE_CHOICES)


class LocationRequest(Request):
    location = models.ForeignKey(Location, editable=False)


class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True, editable=False)

    # Basic Information
    locations = models.ManyToManyField(Location, null=True, blank=True)
    website = models.CharField(max_length=32, null=True, blank=True)
    job = models.CharField(max_length=32, null=True, blank=True)
    hobbies = models.CharField(max_length=64, null=True, blank=True)

    # Avatar
    avatar = models.CharField(max_length=64, editable=False, null=True, blank=True)

    # Gear
    telescopes = models.ManyToManyField(Telescope, null=True, blank=True)
    mounts = models.ManyToManyField(Mount, null=True, blank=True)
    cameras = models.ManyToManyField(Camera, null=True, blank=True)
    focal_reducers = models.ManyToManyField(FocalReducer, null=True, blank=True)
    software = models.ManyToManyField(Software, null=True, blank=True)
    filters = models.ManyToManyField(Filter, null=True, blank=True)
    accessories = models.ManyToManyField(Accessory, null=True, blank=True)

    follows = models.ManyToManyField('self', null=True, blank=True, related_name='followers')

    def __unicode__(self):
        return "%s' profile" % self.user.username

    def get_absolute_url(self):
        return '/users/%s' % self.user.username

    class Meta:
        app_label = 'astrobin'


def create_user_profile(sender, instance, created, **kwargs):  
    if created:
        profile, created = UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User)

