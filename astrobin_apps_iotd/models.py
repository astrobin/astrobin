from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from astrobin.models import Image
from astrobin_apps_iotd.permissions import may_elect_iotd, may_toggle_submission_image, may_toggle_vote_image


class IotdQueueSortOrder:
    NEWEST_FIRST = 'NEWEST_FIRST'
    OLDEST_FIRST = 'OLDEST_FIRST'

class IotdSubmission(models.Model):
    submitter = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['image', 'submitter']

    def __str__(self):
        return "IOTD submission by %s: %s (%d)" % (
            self.submitter.username,
            self.image.title,
            self.image.pk)

    @classmethod
    def last_for_image(cls, pk):
        submissions = IotdSubmission.objects.filter(image__pk=pk).order_by('date')
        limit = settings.IOTD_SUBMISSION_MIN_PROMOTIONS
        return submissions[limit - 1: limit]

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
    reviewer = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['reviewer', 'image']

    def __str__(self):
        return "IOTD vote by %s: %s" % (
            self.reviewer.username,
            self.image.title)

    @classmethod
    def last_for_image(cls, pk):
        votes = IotdVote.objects.filter(image__pk=pk).order_by('date')
        limit = settings.IOTD_REVIEW_MIN_PROMOTIONS
        return votes[limit - 1:limit]

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
    image = models.OneToOneField(Image, on_delete=models.CASCADE)
    date = models.DateField(unique=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return "IOTD: %s" % self.image.title

    def clean(self):
        may, reason = may_elect_iotd(self.judge, self.image)
        if not may:
            raise ValidationError(reason)

    def save(self, *args, **kwargs):
        # Force validation on save
        self.full_clean()
        return super(Iotd, self).save(*args, **kwargs)


class IotdHiddenImage(models.Model):
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, null=False, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
        unique_together = ('user', 'image')

    def __str__(self):
        return "IOTD hidden image: %d / %s" % (self.user.pk, self.image.get_id())


class IotdDismissedImage(models.Model):
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, null=False, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
        unique_together = ('user', 'image')

    def __str__(self):
        return "IOTD dismissed image: %d / %s" % (self.user.pk, self.image.get_id())


class TopPickNominationsArchive(models.Model):
    image = models.OneToOneField(Image, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-image__published']


class TopPickArchive(models.Model):
    image = models.OneToOneField(Image, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-image__published']



class IotdStaffMemberSettings(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='iotd_staff_member_settings',
    )

    queue_sort_order = models.CharField(
        max_length=16,
        choices=(
            (IotdQueueSortOrder.NEWEST_FIRST, _('Newest first')),
            (IotdQueueSortOrder.OLDEST_FIRST, _('Oldest first'))
        ),
        default=IotdQueueSortOrder.NEWEST_FIRST,
    )


class IotdSubmissionQueueEntry(models.Model):
    submitter = models.ForeignKey(
        User,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='submission_queue_entries',
    )

    image = models.ForeignKey(
        Image,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='submission_queue_entries',
    )

    published = models.DateTimeField(
        null=False,
        blank=False,
    )

    class Meta:
        unique_together = ('submitter', 'image',)
        ordering = ('published',)


class IotdReviewQueueEntry(models.Model):
    reviewer = models.ForeignKey(
        User,
        null = False,
        blank = False,
        on_delete = models.CASCADE,
        related_name = 'review_queue_entries',
    )

    image = models.ForeignKey(
        Image,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='review_queue_entries',
    )

    last_submission_timestamp = models.DateTimeField(
        null=False,
        blank=False,
    )

    class Meta:
        unique_together = ('reviewer', 'image',)
        ordering = ('last_submission_timestamp',)


class IotdJudgementQueueEntry(models.Model):
    judge = models.ForeignKey(
        User,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='judgement_queue_entry',
    )

    image = models.ForeignKey(
        Image,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='judgement_queue_entry',
    )

    last_vote_timestamp = models.DateTimeField(
        null=False,
        blank=False,
    )

    class Meta:
        unique_together = ('judge', 'image',)
        ordering = ('last_vote_timestamp',)
