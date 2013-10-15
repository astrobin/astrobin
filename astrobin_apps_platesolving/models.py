from django.db import models


class Solution(models.Model):
    STATUS_CHOICES = (
        (0, 'missing'),
        (1, 'pending'),
        (2, 'failed'),
        (3, 'success'),
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
    )


    objects_in_field = models.CharField(
        max_length = 128,
        null = True,
        blank = True,
    )

    ra = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 16,
        decimal_places = 14,
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
