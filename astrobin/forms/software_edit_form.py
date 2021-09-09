from astrobin.forms.migratable_gear_item_edit_form import MigratableGearItemEditForm
from astrobin.models import Software


class SoftwareEditForm(MigratableGearItemEditForm):
    class Meta:
        model = Software
        exclude = MigratableGearItemEditForm.Meta.exclude
