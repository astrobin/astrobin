from django.db import models
from django.utils.translation import ugettext_lazy as _
from safedelete.models import SafeDeleteModel


class EquipmentItemKlass:
    SENSOR = "SENSOR"
    CAMERA = "CAMERA"
    TELESCOPE = "TELESCOPE"
    MOUNT = "MOUNT"
    FILTER = "FILTER"
    ACCESSORY = "ACCESSORY"
    SOFTWARE = "SOFTWARE"


class EquipmentItemUsageType:
    IMAGING = "IMAGING"
    GUIDING = "GUIDING"


EQUIPMENT_ITEM_KLASS_CHOICES = (
    (EquipmentItemKlass.SENSOR, _("Sensor")),
    (EquipmentItemKlass.CAMERA, _("Camera")),
    (EquipmentItemKlass.TELESCOPE, _("Telescope")),
    (EquipmentItemKlass.MOUNT, _("Mount")),
    (EquipmentItemKlass.FILTER, _("Filter")),
    (EquipmentItemKlass.ACCESSORY, _("Accessory")),
    (EquipmentItemKlass.SOFTWARE, _("Software")),
)

EQUIPMENT_ITEM_USAGE_TYPE_CHOICES = (
    (EquipmentItemUsageType.IMAGING, _("Imaging")),
    (EquipmentItemUsageType.GUIDING, _("Guiding")),
)


class EquipmentItemGroup(SafeDeleteModel):
    klass = models.CharField(
        max_length=16,
        null=True,
        blank=False,
        choices=EQUIPMENT_ITEM_KLASS_CHOICES
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

    name = models.CharField(
        max_length=128,
        null=False,
        blank=False,
    )
