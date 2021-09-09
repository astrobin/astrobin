from astrobin.forms.migratable_gear_item_edit_form import MigratableGearItemEditForm
from astrobin.models import Mount


class MountEditForm(MigratableGearItemEditForm):
    class Meta:
        model = Mount
        exclude = MigratableGearItemEditForm.Meta.exclude
