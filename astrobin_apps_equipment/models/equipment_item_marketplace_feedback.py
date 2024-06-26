# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext
from safedelete.models import SafeDeleteModel

from astrobin_apps_equipment.types.marketplace_feedback import MarketplaceFeedback
from astrobin_apps_equipment.types.marketplace_feedback_target_type import MarketplaceFeedbackTargetType

EQUIPMENT_ITEM_MARKETPLACE_FEEDBACK_CHOICES = (
    (MarketplaceFeedback.NEGATIVE.value, gettext("Negative")),
    (MarketplaceFeedback.NEUTRAL.value, gettext("Neutral")),
    (MarketplaceFeedback.POSITIVE.value, gettext("Positive")),
)

EQUIPMENT_ITEM_MARKETPLACE_FEEDBACK_TARGET_TYPE_CHOICES = (
    (MarketplaceFeedbackTargetType.SELLER.value, gettext("Seller")),
    (MarketplaceFeedbackTargetType.BUYER.value, gettext("Buyer")),
)


class EquipmentItemMarketplaceFeedback(SafeDeleteModel):
    user = models.ForeignKey(
        User,
        related_name='equipment_item_marketplace_listings_feedbacks_given',
        on_delete=models.SET_NULL,
        null=True,
    )

    recipient = models.ForeignKey(
        User,
        related_name='equipment_item_marketplace_listings_feedbacks_received',
        on_delete=models.CASCADE,
        null=True,
    )

    listing = models.ForeignKey(
        'astrobin_apps_equipment.EquipmentItemMarketplaceListing',
        related_name='feedbacks',
        on_delete=models.CASCADE,
        null=False,
        editable=False,
    )

    created = models.DateTimeField(
        auto_now_add=True,
        null=False,
        editable=False,
    )

    updated = models.DateTimeField(
        auto_now=True,
        null=False,
        editable=False,
    )

    communication_value = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        choices=EQUIPMENT_ITEM_MARKETPLACE_FEEDBACK_CHOICES,
    )

    speed_value = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        choices=EQUIPMENT_ITEM_MARKETPLACE_FEEDBACK_CHOICES,
    )

    accuracy_value = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        choices=EQUIPMENT_ITEM_MARKETPLACE_FEEDBACK_CHOICES,
    )

    packaging_value = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        choices=EQUIPMENT_ITEM_MARKETPLACE_FEEDBACK_CHOICES,
    )

    message = models.TextField(
        null=True,
        blank=True,
    )

    target_type = models.CharField(
        max_length=6,
        choices=EQUIPMENT_ITEM_MARKETPLACE_FEEDBACK_TARGET_TYPE_CHOICES,
    )

    def __str__(self):
        return f'Marketplace listing feedback for listing {self.listing} by {self.user}'

    class Meta:
        ordering = ('-created',)
        unique_together = ('user', 'listing')
