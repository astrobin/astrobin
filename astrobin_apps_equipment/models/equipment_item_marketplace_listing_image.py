from django.contrib.auth.models import User
from django.db import models
from safedelete.models import SafeDeleteModel

from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing
from common.upload_paths import marketplace_listing_upload_path


class EquipmentItemMarketplaceListingImage(SafeDeleteModel):
    user = models.ForeignKey(
        User,
        related_name='equipment_marketplace_listing_images',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )

    listing = models.ForeignKey(
        EquipmentItemMarketplaceListing,
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
        return f'Image by {self.user} for {self.listing if self.listing else "unknown listing"}'
