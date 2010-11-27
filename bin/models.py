from django.db import models

class Gear(models.Model):
	name = models.CharField(max_length=64)
	purchase_date = models.DateTimeField('date purchased')

class Camera(Gear):
	chip_size = models.IntegerField()

class Telescope(Gear):
	focal_length = models.IntegerField()
	aperture = models.IntegerField()

class Mount(Gear):

class FocalReduced(Gear):
	ratio = models.DoubleField()

class Subject(models.Model):
	name = model.CharField(max_length=64)

	# gear
	camera = models.ForeignKey(Camera)
	focal_reducer = models.ForegnKey(FocalReducer)
	telescope = models.ForeignKey(Telescope)
	mount = models.ForeignKey(Mount)

	# data
