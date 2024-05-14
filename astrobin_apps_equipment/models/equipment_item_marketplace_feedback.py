# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext
from safedelete.models import SafeDeleteModel

from astrobin_apps_equipment.types.marketplace_feedback import MarketplaceFeedback
from astrobin_apps_equipment.types.marketplace_feedback_category import MarketplaceFeedbackCategory

EQUIPMENT_ITEM_MARKETPLACE_FEEDBACK_CHOICES = (
    (MarketplaceFeedback.NEGATIVE.value, gettext("Negative")),
    (MarketplaceFeedback.NEUTRAL.value, gettext("Neutral")),
    (MarketplaceFeedback.POSITIVE.value, gettext("Positive")),
)

EQUIPMENT_ITEM_MARKETPLACE_FEEDBACK_CATEGORY_CHOICES = (
    (MarketplaceFeedbackCategory.COMMUNICATION.value, gettext("Communication and friendliness")),
    (MarketplaceFeedbackCategory.SPEED.value, gettext("Speed of delivery")),
    (MarketplaceFeedbackCategory.ACCURACY.value, gettext("Accuracy of item descriptions")),
    (MarketplaceFeedbackCategory.PACKAGING.value, gettext("Packaging quality")),
)


class EquipmentItemMarketplaceFeedback(SafeDeleteModel):
    user = models.ForeignKey(
        User,
        related_name='equipment_item_marketplace_listings_feedbacks_given',
        on_delete=models.CASCADE,
        null=False,
        editable=False,
    )

    line_item = models.ForeignKey(
        'astrobin_apps_equipment.EquipmentItemMarketplaceListingLineItem',
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

    value = models.CharField(
        max_length=16,
        null=False,
        blank=False,
        choices=EQUIPMENT_ITEM_MARKETPLACE_FEEDBACK_CHOICES,
    )

    category = models.CharField(
        max_length=16,
        null=False,
        blank=False,
        choices=EQUIPMENT_ITEM_MARKETPLACE_FEEDBACK_CATEGORY_CHOICES,
    )

    def __str__(self):
        return f'Marketplace listing feedback for line item {self.line_item} by {self.user}: {self.category} {self.value}'

    class Meta:
        ordering = ('-created',)
        unique_together = ('user', 'line_item', 'category')
