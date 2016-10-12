# Python
from datetime import datetime, timedelta

# Django
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy

# AstroBin
from astrobin.models import Image

# This app
from astrobin_apps_iotd.permissions import *


class IotdSubmission(models.Model):
    submitter = models.ForeignKey(User)
    image = models.ForeignKey(Image)
    date = models.DateTimeField(auto_now_add = True)

    class Meta:
        unique_together = ['image', 'submitter']

    def __unicode__(self):
        return "IOTD submission by %s: %s (%d)" % (
            self.submitter.username,
            self.image.title,
            self.image.pk)

    def clean(self):
        may, reason = may_submit_image(self.submitter, self.image)
        if not may:
            raise ValidationError(reason)

    def save(self, *args, **kwargs):
        # Force validationo on save
        self.full_clean()
        return super(IotdSubmission, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse_lazy('iotd_submission_detail', kwargs = {'pk': self.pk})
