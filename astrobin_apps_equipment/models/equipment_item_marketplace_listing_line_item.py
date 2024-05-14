# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext

from astrobin.fields import CURRENCY_CHOICES
from astrobin_apps_equipment.types.marketplace_line_item_condition import MarketplaceLineItemCondition
from astrobin_apps_payments.models import ExchangeRate
from common.models.hashed_model import HashedSafeDeleteModel

EQUIPMENT_ITEM_MARKETPLACE_LISTING_CONDITION_CHOICES = (
    (MarketplaceLineItemCondition.UNOPENED.value, gettext("Unopened")),
    (MarketplaceLineItemCondition.NEW.value, gettext("New")),
    (MarketplaceLineItemCondition.USED.value, gettext("Used")),
    (MarketplaceLineItemCondition.DAMAGED_OR_DEFECTIVE.value, gettext("Damaged or defective")),
    (MarketplaceLineItemCondition.OTHER.value, gettext("Other")),
)


class EquipmentItemMarketplaceListingLineItem(HashedSafeDeleteModel):
    pre_save_sold = None

    user = models.ForeignKey(
        User,
        related_name='created_equipment_item_marketplace_listing_line_items',
        on_delete=models.CASCADE,
        null=False,
        editable=False,
    )

    listing = models.ForeignKey(
        'astrobin_apps_equipment.EquipmentItemMarketplaceListing',
        related_name='line_items',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
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

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    currency = models.CharField(
        max_length=3,
        null=True,
        blank=True,
        choices=CURRENCY_CHOICES,
    )

    # AstroBin will automatically convert prices to CHF to allow for easier filtering.
    price_chf = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
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

    shipping_cost = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    description = models.TextField(
        null=True,
        blank=True,
    )

    item_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    item_object_id = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    item_content_object = GenericForeignKey(
        'item_content_type',
        'item_object_id',
    )

    item_plain_text = models.CharField(
        max_length=256,
        null=True,
        blank=True,
    )

    # This is a denormalized field that is updated automatically.
    item_name = models.CharField(
        editable=False,
        max_length=256,
        null=True,
        blank=True,
    )

    # The reminder to rate the seller has been sent.
    rate_seller_reminder_sent = models.DateTimeField(
        null=True,
        blank=True,
    )

    def clean(self):
        if not self.item_object_id and not self.item_plain_text:
            raise ValidationError("Either item_object_id or item_plain_text must be provided.")

        super().clean()

    def save(self, *args, **kwargs):
        self.update_price_chf()
        self.update_item_name()
        super(EquipmentItemMarketplaceListingLineItem, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from astrobin_apps_equipment.models import EquipmentItemMarketplaceListingLineItemImage
        related_children = EquipmentItemMarketplaceListingLineItemImage.objects.filter(line_item=self)
        for child in related_children:
            child.delete()
        super(EquipmentItemMarketplaceListingLineItem, self).delete(*args, **kwargs)

    def update_price_chf(self):
        if self.price and self.currency:
            if self.currency == 'CHF':
                self.price_chf = self.price
            else:
                exchange_rate = ExchangeRate.objects.filter(source='CHF', target=self.currency).first()
                if exchange_rate:
                    self.price_chf = self.price / exchange_rate.rate

    def update_item_name(self):
        if self.item_content_object:
            self.item_name = str(self.item_content_object)
        else:
            self.item_name = self.item_plain_text

    @property
    def slug(self) -> str:
        return slugify(str(self))

    def __str__(self) -> str:
        return str(self.item_content_object or self.item_plain_text)

    class Meta:
        ordering = ('created',)
