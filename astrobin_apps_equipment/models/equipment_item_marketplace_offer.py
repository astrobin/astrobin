# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from safedelete.models import SafeDeleteModel


class EquipmentItemMarketplaceOffer(SafeDeleteModel):
    user = models.ForeignKey(
        User,
        related_name='equipment_item_marketplace_listings_offers',
        on_delete=models.CASCADE,
        null=False,
        editable=False,
    )

    listing = models.ForeignKey(
        'astrobin_apps_equipment.EquipmentItemMarketplaceListing',
        related_name='offers',
        on_delete=models.CASCADE,
        null=False,
        editable=False,
    )

    line_item = models.ForeignKey(
        'astrobin_apps_equipment.EquipmentItemMarketplaceListingLineItem',
        related_name='offers',
        on_delete=models.CASCADE,
        null=False,
        editable=False,
    )

    created = models.DateTimeField(
        auto_now_add=True,
        null=False,
        editable=False,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f'Marketplace listing line item offer for {self.line_item} by {self.user}: {self.amount}'
