import uuid
from datetime import datetime

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django import forms


class Gear(models.Model):
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name


class Telescope(Gear):
    focal_length = models.IntegerField(null=True, blank=True)
    aperture = models.IntegerField(null=True, blank=True)


class Mount(Gear):
    pass


class Camera(Gear):
    pass


class FocalReducer(Gear):
    ratio = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)


class Software(Gear):
    pass


class Filter(Gear):
    pass


class Accessory(Gear):
    pass


class Subject(models.Model):
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=64)
    latitude = models.DecimalField(max_digits=3, decimal_places=4, null=True, blank=True)
    longitude = models.DecimalField(max_digits=3, decimal_places=4, null=True, blank=True)
    altitude = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.name


class Image(models.Model):
    title = models.CharField(max_length=128)
    subjects = models.ManyToManyField(Subject)
    locations = models.ManyToManyField(Location, null=True, blank=True)
    description = models.TextField()
    filename = models.CharField(max_length=64, editable=False)
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

    class Meta:
        ordering = ('-uploaded', '-id')
        
    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.uploaded = datetime.now()
        super(Image, self).save(*args, **kwargs)


class Acquisition(models.Model):
    date = models.DateField(null=True, blank=True)
    image = models.ForeignKey(Image)


class DeepSky_Acquisition(Acquisition):
    acquisition_type = models.CharField(max_length=2)
    number = models.IntegerField()
    duration = models.IntegerField(null=True, blank=True)
    iso = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return ''


class SolarSystem_Acquisition(Acquisition):
    frames = models.IntegerField()
    fps = models.IntegerField(null=True, blank=True)
    focal_length = models.IntegerField(null=True, blank=True)
    cmi = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2)
    cmii = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2)
    cmiii = models.DecimalField(null=True, blank=True, max_digits=5, decimal_places=2)
    seeing = models.IntegerField(null=True, blank=True)
    transparency = models.IntegerField(null=True, blank=True)
    time = models.CharField(null=True, blank=True, max_length=5)


class ABPOD(models.Model):
	image = models.ForeignKey(Image, unique=True)
	date = models.DateTimeField()
	
	def __unicode__(self):
		return self.image.subjects


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
    
    def __unicode__(self):
        return "%s' profile" % self.user


def create_user_profile(sender, instance, created, **kwargs):  
    if created:
        profile, created = UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User)
