from django.db import models
from django.contrib.auth.models import User
from django import forms

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
	subjects = models.CharField(max_length=128) # comma separated list
	file = models.ImageField(upload_to='images/%Y/%m/%d')

	# gear
	camera = models.CharField(max_length=32)
	focal_reducer = models.CharField(max_length=32)
	telescope = models.CharField(max_length=32)
	mount = models.CharField(max_length=32)

	description = models.TextField()

	def __unicode__(self):
		return ""
