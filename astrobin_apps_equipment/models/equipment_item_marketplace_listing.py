# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext
from safedelete.models import SafeDeleteModel

from astrobin.fields import COUNTRIES, CURRENCY_CHOICES
from astrobin_apps_equipment.types.marketplace_listing_condition import MarketplaceListingCondition
from astrobin_apps_equipment.types.marketplace_shipping_method import MarketplaceShippingMethod

EQUIPMENT_ITEM_MARKETPLACE_LISTING_CONDITION_CHOICES = (
    (MarketplaceListingCondition.UNOPENED.value, gettext("Unopened")),
    (MarketplaceListingCondition.NEW.value, gettext("New")),
    (MarketplaceListingCondition.DAMAGED_OR_DEFECTIVE.value, gettext("Damaged or defective")),
    (MarketplaceListingCondition.OTHER.value, gettext("Other")),
)

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

    sold = models.DateTimeField(
        null=True,
    )

    sold_to = models.ForeignKey(
        User,
        related_name='bought_equipment_item_marketplace_listings',
        on_delete=models.SET_NULL,
        null=True,
    )

    reserved = models.DateTimeField(
        null=True,
    )

    reserved_to = models.ForeignKey(
        User,
        related_name='reserved_equipment_item_marketplace_listings',
        on_delete=models.SET_NULL,
        null=True,
    )

    price = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    currency = models.CharField(
        max_length=3,
        null=True,
        blank=True,
        choices=CURRENCY_CHOICES,
    )

    condition = models.CharField(
        max_length=32,
        null=False,
        blank=False,
        choices=EQUIPMENT_ITEM_MARKETPLACE_LISTING_CONDITION_CHOICES,
    )

    year_of_purchase = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
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

    shipping_cost = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
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

    item_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    item_object_id = models.PositiveIntegerField()
    item_content_object = GenericForeignKey('item_content_type', 'item_object_id')

    def __str__(self):
        return f'Marketplace listing for {self.item_content_object} by {self.user}'
