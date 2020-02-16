from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy
from django.db import models

from astrobin.models import Image
from astrobin_apps_iotd.permissions import may_toggle_submission_image, may_toggle_vote_image, may_elect_iotd


class IotdSubmission(models.Model):
    submitter = models.ForeignKey(User)
    image = models.ForeignKey(Image)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['image', 'submitter']

    def __unicode__(self):
        return "IOTD submission by %s: %s (%d)" % (
            self.submitter.username,
            self.image.title,
            self.image.pk)

    @classmethod
    def first_for_image(cls, image):
        qs = IotdSubmission.objects.filter(image=image).order_by('-date')
        if qs:
            return qs[0]
        return None

    def clean(self):
        may, reason = may_toggle_submission_image(self.submitter, self.image)
        if not may:
            raise ValidationError(reason)

    def save(self, *args, **kwargs):
        # Force validation on save
        self.full_clean()
        return super(IotdSubmission, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse_lazy('iotd_submission_detail', kwargs={'pk': self.pk})


class IotdVote(models.Model):
    reviewer = models.ForeignKey(User)
    image = models.ForeignKey(Image)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['reviewer', 'image']

    def __unicode__(self):
        return "IOTD vote by %s: %s" % (
            self.reviewer.username,
            self.image.title)

    @classmethod
    def first_for_image(cls, image):
        qs = IotdVote.objects.filter(image=image).order_by('-date')
        if qs:
            return qs[0]
        return None

    def clean(self):
        may, reason = may_toggle_vote_image(self.reviewer, self.image)
        if not may:
            raise ValidationError(reason)

    def save(self, *args, **kwargs):
        # Force validation on save
        self.full_clean()
        return super(IotdVote, self).save(*args, **kwargs)


class Iotd(models.Model):
    judge = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    image = models.OneToOneField(Image)
    date = models.DateField(unique=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __unicode__(self):
        return "IOTD: %s" % self.image.title

    def clean(self):
        may, reason = may_elect_iotd(self.judge, self.image)
        if not may:
            raise ValidationError(reason)

    def save(self, *args, **kwargs):
        # Force validation on save
        self.full_clean()
        return super(Iotd, self).save(*args, **kwargs)
