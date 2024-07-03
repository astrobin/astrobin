# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext

from astrobin.fields import COUNTRIES
from astrobin_apps_equipment.types.marketplace_listing_type import MarketplaceListingType
from astrobin_apps_equipment.types.marketplace_shipping_method import MarketplaceShippingMethod
from common.models.hashed_model import HashedSafeDeleteModel
from common.services import AppRedirectionService

EQUIPMENT_ITEM_MARKETPLACE_LISTING_TYPE = {
    (MarketplaceListingType.FOR_SALE.value, gettext("For sale")),
    (MarketplaceListingType.WANTED.value, gettext("Wanted")),
}

EQUIPMENT_ITEM_MARKETPLACE_SHIPPING_METHOD_CHOICES = (
    (MarketplaceShippingMethod.STANDARD_MAIL.value, gettext("Standard mail")),
    (MarketplaceShippingMethod.COURIER.value, gettext("Courier")),
    (MarketplaceShippingMethod.ELECTRONIC.value, gettext("Electronic")),
    (MarketplaceShippingMethod.OTHER.value, gettext("Other")),
)


class EquipmentItemMarketplaceListing(HashedSafeDeleteModel):
    pre_save_approved = None
    pre_save_approved_again = None

    listing_type = models.CharField(
        max_length=8,
        null=False,
        blank=False,
        choices=EQUIPMENT_ITEM_MARKETPLACE_LISTING_TYPE,
        default=MarketplaceListingType.FOR_SALE.value,
    )

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

    first_approved = models.DateTimeField(
        null=True,
    )

    approved = models.DateTimeField(
        null=True,
    )

    approved_by = models.ForeignKey(
        User,
        related_name='approved_equipment_item_marketplace_listings',
        on_delete=models.SET_NULL,
        null=True,
    )

    expiration = models.DateTimeField(
        null=False,
        blank=False,
    )

    title = models.CharField(
        max_length=256,
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

    expired_notification_sent = models.DateTimeField(
        null=True,
    )

    # The reminder to rate the seller has been sent.
    rate_seller_reminder_sent = models.DateTimeField(
        null=True,
        blank=True,
    )

    # The reminder to rate the buyer has been sent.
    rate_buyer_reminder_sent = models.DateTimeField(
        null=True,
        blank=True,
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

        if self.title:
            return self.title
        else:
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
