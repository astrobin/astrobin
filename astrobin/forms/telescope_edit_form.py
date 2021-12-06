from astrobin.forms.migratable_gear_item_edit_form import MigratableGearItemEditForm
from astrobin.models import Telescope


class TelescopeEditForm(MigratableGearItemEditForm):
    class Meta:
        model = Telescope
        exclude = MigratableGearItemEditForm.Meta.exclude
