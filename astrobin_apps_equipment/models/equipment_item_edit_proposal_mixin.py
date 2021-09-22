from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _


class EquipmentItemEditProposalMixin(models.Model):
    edit_proposal_original_properties = models.TextField(
        null=False,
        blank=False,
    )

    edit_proposal_by = models.ForeignKey(
        User,
        null=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_edit_proposals',
    )

    edit_proposal_created = models.DateTimeField(
        auto_now_add=True,
        editable=False,
    )

    edit_proposal_updated = models.DateTimeField(
        auto_now=True,
        editable=False,
    )

    edit_proposal_ip = models.GenericIPAddressField(
        null=True,
        editable=False,
    )

    edit_proposal_comment = models.TextField(
        null=True,
        blank=True,
    )

    edit_proposal_reviewed_by = models.ForeignKey(
        User,
        null=True,
        editable=False,
        on_delete=models.SET_NULL,
        related_name='%(app_label)s_%(class)s_edit_proposals_reviewed',
    )

    edit_proposal_review_timestamp = models.DateTimeField(
        null=True,
        editable=False
    )

    edit_proposal_review_ip = models.GenericIPAddressField(
        null=True,
        editable=False,
    )

    edit_proposal_review_comment = models.TextField(
        null=True,
        blank=True,
    )

    edit_proposal_review_status = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        choices=[
            ('ACCEPTED', _("Accepted")),
            ('REJECTED', _("Rejected")),
            ('SUPERSEDED', _("Superseded"))
        ],
    )

    class Meta:
        abstract = True
