from django.contrib.auth.models import User
from django.db import models

from common.mixins import ThumbnailMixin
from common.models.hashed_model import HashedSafeDeleteModel
from common.upload_paths import marketplace_listing_thumbnail_upload_path, marketplace_listing_upload_path


class EquipmentItemMarketplaceListingLineItemImage(HashedSafeDeleteModel, ThumbnailMixin):
    image_field_name = 'image_file'
    thumbnail_field_name = 'thumbnail_file'

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

    thumbnail_file = models.ImageField(
        upload_to=marketplace_listing_thumbnail_upload_path,
        height_field='thumbnail_h',
        width_field='thumbnail_w',
        max_length=256,
        null=True,
    )

    position = models.PositiveIntegerField(
        default=0,
    )

    w = models.PositiveIntegerField(editable=False, default=0)
    thumbnail_w = models.PositiveIntegerField(editable=False, default=0)

    h = models.PositiveIntegerField(editable=False, default=0)
    thumbnail_h = models.PositiveIntegerField(editable=False, default=0)

    created = models.DateTimeField(
        auto_now_add=True,
        null=False,
        editable=False,
    )

    def save(self, *args, **kwargs):
        # Check if the object already exists and has an image
        if self.pk:
            existing_obj = EquipmentItemMarketplaceListingLineItemImage.objects.get(pk=self.pk)
            existing_image = existing_obj.image_file
        else:
            existing_image = None

        # Save the instance
        super(EquipmentItemMarketplaceListingLineItemImage, self).save(*args, **kwargs)

        # If the image has been updated, create a new thumbnail
        if not existing_image or str(self.image_file) != str(existing_image):
            self.create_thumbnail()

    def __str__(self):
        return f'Image by {self.user} for {self.line_item if self.line_item else "unknown listing"}'
