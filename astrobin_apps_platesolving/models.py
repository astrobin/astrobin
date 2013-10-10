from django.db import models

class Solution(models.Model):
    job_success = models.BooleanField(
        default = False,
    )

    objects_in_field = models.CharField(
        max_length = 128,
        null = True,
        blank = True,
    )

    image_file =  models.ImageField(
        upload_to = 'solutions',
        null = True,
    )

    ra_center_hms = models.CharField(
        null = True,
        blank = True,
        max_length = 12,
    )

    dec_center_dms = models.CharField(
        null = True,
        blank = True,
        max_length = 13,
    )

    pixscale = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 14,
        decimal_places = 10,
    )

    orientation = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 14,
        decimal_places = 10,
    )

    fieldw = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 14,
        decimal_places = 10,
    )

    fieldh = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 14,
        decimal_places = 10,
    )

    fieldunits = models.CharField(
        null = True,
        blank = True,
        max_length = 32,
    )


    def __unicode__(self):
        return "solution_%d" % self.id


    class Meta:
        app_label = 'astrobin_apps_platesolving'
