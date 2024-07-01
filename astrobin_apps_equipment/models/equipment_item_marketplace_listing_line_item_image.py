from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from easy_thumbnails.files import get_thumbnailer

from common.models.hashed_model import HashedSafeDeleteModel
from common.upload_paths import marketplace_listing_thumbnail_upload_path, marketplace_listing_upload_path


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

    def create_thumbnail(self):
        options = {
            'size': (512, 0),
            'crop': True,
            'keep_icc_profile': True,
            'quality': 80,
        }

        thumbnailer = get_thumbnailer(self.image_file)
        thumbnail = thumbnailer.get_thumbnail(options)

        thumb_io = BytesIO()
        with thumbnail.open('rb') as thumb_file:
            thumb_io.write(thumb_file.read())
            thumb_io.seek(0)

        self.thumbnail_file.save(thumbnail.name, ContentFile(thumb_io.read()))

        thumb_io.close()

    def __str__(self):
        return f'Image by {self.user} for {self.line_item if self.line_item else "unknown listing"}'
