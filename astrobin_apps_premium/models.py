from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


class DataLossCompensationRequest(models.Model):
    user = models.ForeignKey(
        User,
        editable=False
    )

    created = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )

    requested_compensation = models.CharField(
        choices=(
            ('NOT_AFFECTED', _("I wasn't really affected by the data loss")),
            ('NOT_REQUIRED', _("I don't require compensation: I want to support AstroBin")),
            ('1_MO_ULTIMATE', _("I would like to try AstroBin Ultimate for free for 1 month")),
            ('3_MO_ULTIMATE', _("I feel entitled to AstroBin Ultimate for free for 3 months")),
            ('6_MO_ULTIMATE', _("I feel entitled to AstroBin Ultimate for free for 6 months")),
        ),
        max_length=14,
        verbose_name=_("Requested compensation"),
        help_text=_("Please indicate if and how much you would like to be compensated.")
    )
