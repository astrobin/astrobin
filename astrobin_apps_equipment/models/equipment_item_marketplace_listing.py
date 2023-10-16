# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext
from safedelete.models import SafeDeleteModel

from astrobin.fields import COUNTRIES
from astrobin_apps_equipment.types.marketplace_shipping_method import MarketplaceShippingMethod


EQUIPMENT_ITEM_MARKETPLACE_SHIPPING_METHOD_CHOICES = (
    (MarketplaceShippingMethod.STANDARD_MAIL.value, gettext("Standard mail")),
    (MarketplaceShippingMethod.COURIER.value, gettext("Courier")),
    (MarketplaceShippingMethod.ELECTRONIC.value, gettext("Electronic")),
    (MarketplaceShippingMethod.OTHER.value, gettext("Other")),
)


class EquipmentItemMarketplaceListing(SafeDeleteModel):
    user = models.ForeignKey(
        User,
        related_name='created_equipment_item_marketplace_listings',
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

    expiration = models.DateTimeField(
        null=False,
        blank=False,
    )

    description = models.TextField(
        null=True,
        blank=True,
    )

    delivery_by_buyer_pick_up = models.BooleanField(
        default=True,
    )

    delivery_by_seller_delivery = models.BooleanField(
        default=True,
    )

    delivery_by_shipping = models.BooleanField(
        default=False,
    )

    shipping_method = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        choices=EQUIPMENT_ITEM_MARKETPLACE_SHIPPING_METHOD_CHOICES,
    )

    latitude = models.FloatField(
        null=True,
        blank=True,
    )

    longitude = models.FloatField(
        null=True,
        blank=True,
    )

    country = models.CharField(
        max_length=2,
        null=True,
        blank=True,
        choices=COUNTRIES
    )

    def __str__(self):
        return f'Marketplace listing by {self.user}'
