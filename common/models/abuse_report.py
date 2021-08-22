from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


ABUSE_REPORT_REASON = (
    ('SPAM', _('This content is spam and/or fraudulent')),
    ('OFFENSIVE', _('This content is offensive (e.g. hate speech, harassment, violence, bullying, mocking, etc...')),
    ('IP', _('This content infringes on someone\'s intellectual property')),
    ('OTHER', _('Other'))
)

ABUSE_REPORT_DECISION_CONFIRMED = 'CONFIRMED'
ABUSE_REPORT_DECISION_OVERRULED = 'OVERRULED'
ABUSE_REPORT_DECISION = (
    (ABUSE_REPORT_DECISION_CONFIRMED, _('Confirmed')),
    (ABUSE_REPORT_DECISION_OVERRULED, _('Overruled')),
)


class AbuseReport(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.TextField()
    content_object = GenericForeignKey('content_type', 'object_id')

    content_owner = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='abuse_reports_received'
    )

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='abuse_reports'
    )

    created = models.DateTimeField(
        null=True,
        blank=True,
        auto_now_add=True
    )

    reason = models.CharField(
        null=True,
        blank=True,
        max_length=16,
        choices=ABUSE_REPORT_REASON,
        verbose_name=_('Reason'),
    )

    additional_information = models.CharField(
        null=True,
        blank=True,
        max_length=500,
        verbose_name=_('Additional information (optional)'),
    )

    moderated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='abuse_reports_moderated'
    )

    moderation_datetime = models.DateTimeField(
        null=True,
        blank=True
    )

    decision = models.CharField(
        null=True,
        blank=True,
        max_length=16,
        choices=ABUSE_REPORT_DECISION
    )
