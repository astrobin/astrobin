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


class IotdSubmitterSeenImage(models.Model):
    user = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    image = models.ForeignKey(Image, null=False, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
        unique_together = ('user', 'image')

    def __str__(self):
        return "IOTD Submitter seen image: %d / %s" % (self.user.pk, self.image.get_id())


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


class IotdStats(models.Model):
    """
    Statistics about the IOTD and TPN systems.
    IOTD = Image of the day
    TP = Top pick
    TPN = Top pick nomination
    """

    created = models.DateTimeField(auto_now_add=True)

    # Period of time covered by the stats.
    days = models.PositiveSmallIntegerField()

    # Distinct winners.
    distinct_iotd_winners = models.PositiveIntegerField()
    distinct_tp_winners = models.PositiveIntegerField()
    distinct_tpn_winners = models.PositiveIntegerField()

    # Total awarded images.
    total_iotds = models.PositiveIntegerField()
    total_tps = models.PositiveIntegerField()
    total_tpns = models.PositiveIntegerField()

    # Total submitted images.
    total_submitted_images = models.PositiveIntegerField()

    # Breakdown by subject type.
    total_deep_sky_images = models.PositiveIntegerField()
    total_solar_system_images = models.PositiveIntegerField()
    total_wide_field_images = models.PositiveIntegerField()
    total_star_trails_images = models.PositiveIntegerField()
    total_northern_lights_images = models.PositiveIntegerField()
    total_noctilucent_clouds_images = models.PositiveIntegerField()

    deep_sky_iotds = models.PositiveIntegerField()
    solar_system_iotds = models.PositiveIntegerField()
    wide_field_iotds = models.PositiveIntegerField()
    star_trails_iotds = models.PositiveIntegerField()
    northern_lights_iotds = models.PositiveIntegerField()
    noctilucent_clouds_iotds = models.PositiveIntegerField()

    deep_sky_tps = models.PositiveIntegerField()
    solar_system_tps = models.PositiveIntegerField()
    wide_field_tps = models.PositiveIntegerField()
    star_trails_tps = models.PositiveIntegerField()
    northern_lights_tps = models.PositiveIntegerField()
    noctilucent_clouds_tps = models.PositiveIntegerField()

    deep_sky_tpns = models.PositiveIntegerField()
    solar_system_tpns = models.PositiveIntegerField()
    wide_field_tpns = models.PositiveIntegerField()
    star_trails_tpns = models.PositiveIntegerField()
    northern_lights_tpns = models.PositiveIntegerField()
    noctilucent_clouds_tpns = models.PositiveIntegerField()

    # Breakdown by data source.
    total_backyard_images = models.PositiveIntegerField()
    total_traveller_images = models.PositiveIntegerField()
    total_own_remote_images = models.PositiveIntegerField()
    total_amateur_hosting_images = models.PositiveIntegerField()
    total_public_amateur_data_images = models.PositiveIntegerField()
    total_pro_data_images = models.PositiveIntegerField()
    total_mix_images = models.PositiveIntegerField()
    total_other_images = models.PositiveIntegerField()
    total_unknown_images = models.PositiveIntegerField()

    backyard_iotds = models.PositiveIntegerField()
    traveller_iotds = models.PositiveIntegerField()
    own_remote_iotds = models.PositiveIntegerField()
    amateur_hosting_iotds = models.PositiveIntegerField()
    public_amateur_data_iotds = models.PositiveIntegerField()
    pro_data_iotds = models.PositiveIntegerField()
    mix_iotds = models.PositiveIntegerField()
    other_iotds = models.PositiveIntegerField()
    unknown_iotds = models.PositiveIntegerField()

    backyard_tps = models.PositiveIntegerField()
    traveller_tps = models.PositiveIntegerField()
    own_remote_tps = models.PositiveIntegerField()
    amateur_hosting_tps = models.PositiveIntegerField()
    public_amateur_data_tps = models.PositiveIntegerField()
    pro_data_tps = models.PositiveIntegerField()
    mix_tps = models.PositiveIntegerField()
    other_tps = models.PositiveIntegerField()
    unknown_tps = models.PositiveIntegerField()

    backyard_tpns = models.PositiveIntegerField()
    traveller_tpns = models.PositiveIntegerField()
    own_remote_tpns = models.PositiveIntegerField()
    amateur_hosting_tpns = models.PositiveIntegerField()
    public_amateur_data_tpns = models.PositiveIntegerField()
    pro_data_tpns = models.PositiveIntegerField()
    mix_tpns = models.PositiveIntegerField()
    other_tpns = models.PositiveIntegerField()
    unknown_tpns = models.PositiveIntegerField()

    class Meta:
        ordering = ('-created',)


class IotdStaffMemberScore(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='iotd_staff_member_score',
    )

    created = models.DateTimeField(
        auto_now_add=True,
    )

    period_start = models.DateTimeField(
        null=False,
        blank=False,
    )

    period_end = models.DateTimeField(
        null=False,
        blank=False,
    )

    score = models.DecimalField(
        default=0,
        max_digits=8,
        decimal_places=2,
    )

    active_days = models.PositiveSmallIntegerField(
        default=0,
    )

    promotions_dismissals_accuracy_ratio = models.DecimalField(
        default=0,
        max_digits=5,
        decimal_places=2,
    )

    promotions = models.PositiveIntegerField(default=0)
    wasted_promotions = models.PositiveIntegerField(default=0)
    missed_iotd_promotions = models.PositiveIntegerField(default=0)
    missed_tp_promotions = models.PositiveIntegerField(default=0)
    missed_tpn_promotions = models.PositiveIntegerField(default=0)
    promotions_to_tpn = models.PositiveIntegerField(default=0)
    promotions_to_tp = models.PositiveIntegerField(default=0)
    promotions_to_iotd = models.PositiveIntegerField(default=0)

    dismissals = models.PositiveIntegerField(default=0)
    correct_dismissals = models.PositiveIntegerField(default=0)
    missed_dismissals = models.PositiveIntegerField(default=0)
    dismissals_to_tpn = models.PositiveIntegerField(default=0)
    dismissals_to_tp = models.PositiveIntegerField(default=0)
    dismissals_to_iotd = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('-score',)
