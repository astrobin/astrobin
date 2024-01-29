# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext

from astrobin.fields import COUNTRIES
from astrobin_apps_equipment.types.marketplace_shipping_method import MarketplaceShippingMethod
from common.models.hashed_model import HashedSafeDeleteModel
from common.services import AppRedirectionService

EQUIPMENT_ITEM_MARKETPLACE_SHIPPING_METHOD_CHOICES = (
    (MarketplaceShippingMethod.STANDARD_MAIL.value, gettext("Standard mail")),
    (MarketplaceShippingMethod.COURIER.value, gettext("Courier")),
    (MarketplaceShippingMethod.ELECTRONIC.value, gettext("Electronic")),
    (MarketplaceShippingMethod.OTHER.value, gettext("Other")),
)


class EquipmentItemMarketplaceListing(HashedSafeDeleteModel):
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

    approved = models.DateTimeField(
        null=True,
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

    city = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    bundle_sale_only = models.BooleanField(
        default=False,
    )

    def delete(self, *args, **kwargs):
        from astrobin_apps_equipment.models import EquipmentItemMarketplaceListingLineItem
        related_children = EquipmentItemMarketplaceListingLineItem.objects.filter(listing=self)
        for child in related_children:
            child.delete()
        super(EquipmentItemMarketplaceListing, self).delete(*args, **kwargs)

    def __str__(self):
        if self.line_items.count() == 0:
            return f'Marketplace listing by {self.user}'

        return ' / '.join([str(item) for item in self.line_items.all()])

    def get_absolute_url(self):
        return AppRedirectionService.redirect(f'/equipment/marketplace/listing/{self.hash}')

    @property
    def slug(self):
        return '-'.join(x.slug for x in self.line_items.all())

    class Meta:
        ordering = ['-approved', '-updated']
        indexes = [
            models.Index(fields=['approved', 'updated']),
            models.Index(fields=['country']),
        ]
