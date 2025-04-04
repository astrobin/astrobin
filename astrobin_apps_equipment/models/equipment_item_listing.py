# -*- coding: utf-8 -*-


from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import CASCADE, SET_NULL
from django.utils.translation import gettext
from safedelete.models import SafeDeleteModel

from astrobin_apps_equipment.models.equipment_retailer import EquipmentRetailer
from astrobin_apps_equipment.types import StockStatus
from astrobin_apps_equipment.types.listing_type import EquipmentListingType

EQUIPMENT_ITEM_LISTING_STOCK_CHOICES = (
    # Please note: "UNKNOWN" means that this vendor supports stock polling, but the stock for a particular item is
    # not known. Vendors that do not support stock polling will have a `null` stock status instead.
    (StockStatus.UNKNOWN.value, gettext("Unknown")),
    (StockStatus.BACK_ORDER.value, gettext("Back order")),
    (StockStatus.IN_STOCK.value, gettext("In stock")),
    (StockStatus.OUT_OF_STOCK.value, gettext("Out of stock")),
)

EQUIPMENT_ITEM_LISTING_TYPE_CHOICES = (
    (EquipmentListingType.SELLS.value, gettext("Sells")),
    (EquipmentListingType.PAIRS_WELL.value, gettext("Pairs well")),
)

class EquipmentItemListing(SafeDeleteModel):
    created_by = models.ForeignKey(
        User,
        related_name='created_equipment_item_listings',
        on_delete=SET_NULL,
        null=True,
        editable=False,
    )

    created = models.DateTimeField(
        auto_now_add=True,
        null=False,
        editable=False
    )

    updated = models.DateTimeField(
        auto_now=True,
        null=False,
        editable=False
    )

    listing_type = models.CharField(
        max_length=16,
        default=EquipmentListingType.SELLS.value,
        choices=EQUIPMENT_ITEM_LISTING_TYPE_CHOICES,
    )

    # This is the full name (brand + item name) of the item on AstroBin.
    item_full_name = models.CharField(
        max_length=256,
        null=True,
        blank=True,
    )

    # This name might be something different from the item's name on AstroBin, in case the retailer calls it something
    # else.
    name = models.CharField(
        max_length=256,
        null=False,
        blank=False,
    )

    name_de = models.CharField(
        max_length=256,
        null=True,
        blank=True,
    )

    retailer = models.ForeignKey(
        EquipmentRetailer,
        on_delete=CASCADE,
        null=False
    )

    url = models.URLField(
        max_length=512,
    )

    url_de = models.URLField(
        null=True,
        blank=True,
        max_length=512,
    )

    image_url = models.URLField(
        max_length=512,
        null=True,
        blank=True,
    )

    sku = models.CharField(
        max_length=32,
        null=True,
        blank=True,
    )

    stock_status = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        choices=EQUIPMENT_ITEM_LISTING_STOCK_CHOICES,
    )

    stock_amount = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    item_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    item_object_id = models.PositiveIntegerField()
    item_content_object = GenericForeignKey('item_content_type', 'item_object_id')

    def __str__(self):
        return "%s by %s" % (self.name, self.retailer)

    class Meta:
        unique_together = (
            'name',
            'retailer',
        )
