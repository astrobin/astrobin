# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.db import models

from astrobin_apps_equipment.models.equipment_item_marketplace_offer import EquipmentItemMarketplaceOfferStatus


# This class is used to have a reference object to gather all listing offers by a user.
# This grouping can be used for notifications.
class EquipmentItemMarketplaceMasterOffer(models.Model):
    # UUID of the master offer. This is used to group line item offers part of the same master offer.
    master_offer_uuid = models.CharField(
        max_length=36,
        null=False,
        editable=False,
        unique=True,
    )

    user = models.ForeignKey(
        User,
        related_name='equipment_item_marketplace_listings_master_offers',
        on_delete=models.CASCADE,
        null=False,
        editable=False,
    )

    listing = models.ForeignKey(
        'astrobin_apps_equipment.EquipmentItemMarketplaceListing',
        related_name='master_offers',
        on_delete=models.CASCADE,
        null=False,
        editable=False,
    )

    # We will synchronize the offer status with the master offer status. Offers are always accepted/rejected as one, at
    # least from our UI. We will use changes to this status here to emit notifications (see signals).
    status = models.CharField(
        max_length=10,
        choices=EquipmentItemMarketplaceOfferStatus.choices(),
        default=EquipmentItemMarketplaceOfferStatus.PENDING.value,
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

    class Meta:
        ordering = ('-created',)
        unique_together = ('user', 'listing', 'master_offer_uuid')

    def __str__(self):
        return f'Marketplace listing master offer for {self.listing} by {self.user}'
