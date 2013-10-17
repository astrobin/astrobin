# Django
from django.db import models

# This app
from astrobin_apps_platesolving.solver import Solver


class Solution(models.Model):
    STATUS_CHOICES = (
        (Solver.MISSING, 'Missing'),
        (Solver.PENDING, 'Pending'),
        (Solver.FAILED,  'Failed'),
        (Solver.SUCCESS, 'Success'),
    )

    status = models.PositiveIntegerField(
        default = 0,
        choices = STATUS_CHOICES,
    )

    submission_id = models.PositiveIntegerField(
        null = True,
        blank = True,
    )


    image_file = models.ImageField(
        upload_to = 'solutions',
        null = True,
        blank = True,
    )


    objects_in_field = models.CharField(
        max_length = 1024,
        null = True,
        blank = True,
    )

    ra = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 3,
    )

    dec = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 3,
    )

    pixscale = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 3,
    )

    orientation = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 3,
    )

    radius = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 3,
    )


    def __unicode__(self):
        return "solution_%d" % self.id


    class Meta:
        app_label = 'astrobin_apps_platesolving'
