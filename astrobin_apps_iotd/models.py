# Python
from datetime import datetime, timedelta

# Django
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

# AstroBin
from astrobin.models import Image


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
        if self.image.is_wip:
            raise ValidationError(_(
                "Images in the staging area cannot be submitted for IOTD"))

        if self.image.uploaded < datetime.now() - timedelta(weeks = 4):
            raise ValidationError(_(
                "You cannot submit an image uploaded less than 4 weeks ago"))

        if not self.submitter.groups.filter(name = 'iotd_submitters').exists():
            raise ValidationError(_(
                "The submitter must be in the iotd_submitters group"))

    def save(self, *args, **kwargs):
        # Force validationo on save
        self.full_clean()
        return super(IotdSubmission, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse_lazy('iotd_submission_detail', kwargs = {'pk': self.pk})
