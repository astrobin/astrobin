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
	pass

class FocalReducer(Gear):
	ratio = models.DecimalField(max_digits=3, decimal_places=2)

class Subject(models.Model):
	name = models.CharField(max_length=64)

class Image(models.Model):
	subject = models.ForeignKey(Subject)

	# gear
	camera = models.ForeignKey(Camera)
	focal_reducer = models.ForeignKey(FocalReducer)
	telescope = models.ForeignKey(Telescope)
	mount = models.ForeignKey(Mount)

	# data

