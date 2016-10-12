# Python
from datetime import datetime, timedelta

# Django
from django.db import models
from django.conf import settings
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
            msg = "Images in the staging area cannot be submitted for IOTD."
            raise ValidationError(_(msg))

        weeks = settings.IOTD_SUBMISSION_WINDOW_WEEKS
        window_start = datetime.now() - timedelta(weeks = weeks)
        if self.image.uploaded < window_start:
            msg = "You cannot submit an image that was uploaded more than %(weeks)s weeks ago."
            raise ValidationError(_(msg) % {'weeks': weeks})

        if not self.submitter.groups.filter(name = 'iotd_submitters').exists():
            msg = "You are not a member of the IOTD Submitters board."
            raise ValidationError(_(msg))

        others_today = IotdSubmission.objects.filter(
            submitter = self.submitter,
            date__gt = datetime.now().date() - timedelta(1))
        if others_today.count() >= settings.IOTD_SUBMISSION_MAX_PER_DAY:
            msg = "You have already submitted the maximum allowed number of IOTD Submissions today."
            raise ValidationError(_(msg))

    def save(self, *args, **kwargs):
        # Force validationo on save
        self.full_clean()
        return super(IotdSubmission, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse_lazy('iotd_submission_detail', kwargs = {'pk': self.pk})
