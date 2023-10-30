from django.contrib.auth.models import User
from django.db import models

from common.models.hashed_model import HashedSafeDeleteModel
from common.upload_paths import marketplace_listing_upload_path


class EquipmentItemMarketplaceListingLineItemImage(HashedSafeDeleteModel):
    user = models.ForeignKey(
        User,
        related_name='equipment_marketplace_listing_images',
        on_delete=models.CASCADE,
        null=False,
    )

    line_item = models.ForeignKey(
        'astrobin_apps_equipment.EquipmentItemMarketplaceListingLineItem',
        related_name='images',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    image_file = models.ImageField(
        upload_to=marketplace_listing_upload_path,
        height_field='h',
        width_field='w',
        max_length=256,
        null=True,
    )

    w = models.PositiveIntegerField(editable=False, default=0)

    h = models.PositiveIntegerField(editable=False, default=0)

    created = models.DateTimeField(
        auto_now_add=True,
        null=False,
        editable=False,
    )

    def __str__(self):
        return f'Image by {self.user} for {self.line_item if self.line_item else "unknown listing"}'
