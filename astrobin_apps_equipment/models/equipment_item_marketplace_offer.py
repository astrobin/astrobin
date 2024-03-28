# -*- coding: utf-8 -*-
from enum import Enum

from django.contrib.auth.models import User
from django.db import models


class EquipmentItemMarketplaceOfferStatus(Enum):
    PENDING = 'PENDING'
    ACCEPTED = 'ACCEPTED'
    REJECTED = 'REJECTED'

    @classmethod
    def choices(cls):
        return tuple((i.name, i.value) for i in cls)


class EquipmentItemMarketplaceOffer(models.Model):
    pre_save_amount_changed = None

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

    master_offer = models.ForeignKey(
        'astrobin_apps_equipment.EquipmentItemMarketplaceMasterOffer',
        related_name='offers',
        on_delete=models.CASCADE,
        null=True,
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

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=10,
        choices=EquipmentItemMarketplaceOfferStatus.choices(),
        default=EquipmentItemMarketplaceOfferStatus.PENDING.value,
        null=False,
        editable=False,
    )

    class Meta:
        ordering = ('-created',)
        unique_together = ('user', 'line_item')

    def __str__(self):
        return f'Marketplace listing line item offer for {self.line_item} by {self.user}: {self.amount}'
