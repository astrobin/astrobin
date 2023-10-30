# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext
from safedelete.models import SafeDeleteModel

from astrobin_apps_equipment.types.marketplace_feedback import MarketplaceFeedback

EQUIPMENT_ITEM_MARKETPLACE_FEEDBACK_CHOICES = (
    (MarketplaceFeedback.NEGATIVE.value, gettext("Negative")),
    (MarketplaceFeedback.NEUTRAL.value, gettext("Neutral")),
    (MarketplaceFeedback.POSITIVE.value, gettext("Positive")),
)


class EquipmentItemMarketplaceFeedback(SafeDeleteModel):
    user = models.ForeignKey(
        User,
        related_name='equipment_item_marketplace_listings_feedbacks_given',
        on_delete=models.CASCADE,
        null=False,
        editable=False,
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

    value = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        choices=EQUIPMENT_ITEM_MARKETPLACE_FEEDBACK_CHOICES,
    )

    text = models.TextField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f'Marketplace listing feedback for {self.listing} by {self.user}: {self.value}'
