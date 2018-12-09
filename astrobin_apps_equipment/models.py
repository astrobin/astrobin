from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _
from safedelete.models import SafeDeleteModel

from astrobin_apps_equipment import constants
from astrobin_apps_equipment.utils import (
    brand_logo_upload_to, equipment_item_photo_upload_to
)

MODERATION_STATUS_CHOICES = (
    (constants.MODERATION_PENDING, _("Pending")),
    (constants.MODERATION_REJECTED, _("Rejected")),
    (constants.MODERATION_APPROVED, _("Approved"))
)


class Brand(SafeDeleteModel):
    # Fields proper.

    name = models.CharField(
        max_length=256,
        verbose_name=_("Name"),
        unique=True
    )

    website = models.URLField(
        verbose_name=_("Website"),
        help_text=_("The official website of this brand"),
        unique=True,
    )

    logo = models.ImageField(
        upload_to=brand_logo_upload_to
    )

    # Meta fields.

    created = models.DateTimeField(
        auto_now_add=True,
        editable=False
    )

    created_by = models.ForeignKey(
        User,
        editable=False,
        related_name="equipment_brands_created"
    )

    updated = models.DateTimeField(
        auto_now=True,
        editable=False
    )

    updated_by = models.ForeignKey(
        User,
        editable=False
    )

    moderation_status = models.CharField(
        max_length=8,
        choices=MODERATION_STATUS_CHOICES,
        default=constants.MODERATION_PENDING,
        editable=False
    )

    moderated_by = models.ForeignKey(
        User,
        editable=False,
        related_name="equipment_brands_moderated"
    )

    class Meta:
        ordering = ['name']


class EquipmentItem(models.Model):
    # Choices.

    EQUIPMENT_ITEM_CATEGORIES = (
        (constants.EQUIPMENT_ITEM_CATEGORY_OPTICAL, _("Optical system")),
        (constants.EQUIPMENT_ITEM_CATEGORY_DETECTOR, _("Light detector")),
        (constants.EQUIPMENT_ITEM_CATEGORY_TRACKER, _("Target tracker")),
        (constants.EQUIPMENT_ITEM_CATEGORY_ACCESSORY, _("Accessory")),
        (constants.EQUIPMENT_ITEM_CATEGORY_SOFTWARE, _("Software"))
    )

    EQUIPMENT_ITEM_SUBCATEGORIES = (
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_TELESCOPE, _("Telescope")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_CAMERA_LENS, _("Camera lens")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_FOCAL_REDUCER, _("Focal reducer")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_DIAGONAL, _("Diagonal")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_FIELD_CORRECTOR, _("Field corrector")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_EYEPIECE, _("Eyepiece")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_FILTER_L, _("Luminance filter")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_FILTER_R, _("Red filter")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_FILTER_G, _("Green filter")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_FILTER_B, _("Blue filter")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_FILTER_HA, _("Hydrogen Alpha filter")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_FILTER_SII, _("Sulfur II filter")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_FILTER_OIII, _("Oxygen III filter")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_FILTER_LP, _("Light pollution filter")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_FILTER_SOLAR, _("Solar filter")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_OPTICAL_FILTER_LUNAR, _("Lunar filter")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_DETECTOR_CCD, _("CCD camera")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_DETECTOR_DSLR, _("DSLR camera")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_DETECTOR_MIRRORLESS, _("Mirrorless camera")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_DETECTOR_FILM, _("Film camera")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_DETECTOR_GUIDER, _("Guide camera")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_TRACKER_EQ_MOUNT, _("Equatorial mount")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_TRACKER_ALTAZ_MOUNT, _("Alt-azimuth mount")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_TRACKER_BARN_DOOR, _("Barn door tracker")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_TRACKER_TRIPOD, _("Tripod")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_TRACKER_PIER, _("Pier")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_ACCESSORY_ADAPTER, _("Adapter")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_ACCESSORY_FOCUS_MASK, _("Focus mask")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_ACCESSORY_FOCUSER, _("Focuser")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_ACCESSORY_ARTIFICIAL_FLAT_FIELD, _("Artificial flat field")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_ACCESSORY_DEW_CONTROL, _("Dew control")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_ACCESSORY_FILTER_WHEEL, _("Filter wheel")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_ACCESSORY_INTERVALOMETER, _("Intervalometer")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_ACCESSORY_WEATHER_STATION, _("Weather station")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_SOFTWARE_OBSERVATORY_CONTROL, _("Observatory control")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_SOFTWARE_DATA_ACQUISITION, _("Data acquisition")),
        (constants.EQUIPMENT_ITEM_SUBCATEGORY_SOFTWARE_DATA_PROCESSING, _("Data processing"))
    )

    # Fields proper.

    brand = models.ForeignKey(
        'Brand'
    )

    name = models.CharField(
        max_length=256,
        verbose_name=_("Name")
    )

    website = models.URLField(
        verbose_name=_("Website"),
        help_text=_("The official website of this equipment item"),
        null=True
    )

    photo = models.ImageField(
        upload_to=equipment_item_photo_upload_to
    )

    category = models.CharField(
        verbose_name=_("Category"),
        help_text=_("The broad category that best defines this item."),
        max_length=32,
        choices=EQUIPMENT_ITEM_CATEGORIES

    )

    subcategory = models.CharField(
        verbose_name=_("Subcategory"),
        help_text=_("The subcategory that best defines this item."),
        max_length=64,
        choices=EQUIPMENT_ITEM_SUBCATEGORIES
    )

    # Meta fields.

    created = models.DateTimeField(
        auto_now_add=True,
        editable=False
    )

    created_by = models.ForeignKey(
        User,
        related_name="equipment_items_created"
    )

    updated = models.DateTimeField(
        auto_now=True,
        editable=False
    )

    updated_by = models.ForeignKey(
        User,
        editable=False
    )

    moderation_status = models.CharField(
        max_length=8,
        choices=MODERATION_STATUS_CHOICES,
        default=constants.MODERATION_PENDING,
        editable=False
    )

    moderated_by = models.ForeignKey(
        User,
        editable=False,
        related_name="equipment_items_moderated"
    )

    class Meta:
        ordering = ['brand', 'name']
        unique_together = (
            ('brand', 'name')
        )
