from django.db import models
from django.contrib.auth.models import User

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
	subject = models.ForeignKey(Subject)

	# gear
	camera = models.ForeignKey(Camera)
	focal_reducer = models.ForeignKey(FocalReducer)
	telescope = models.ForeignKey(Telescope)
	mount = models.ForeignKey(Mount)

	description = models.TextField()

	def __unicode__(self):
		return self.subject.name
