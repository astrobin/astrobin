from astrobin.forms.migratable_gear_item_edit_form import MigratableGearItemEditForm
from astrobin.models import Accessory


class AccessoryEditForm(MigratableGearItemEditForm):
    class Meta:
        model = Accessory
        exclude = MigratableGearItemEditForm.Meta.exclude
