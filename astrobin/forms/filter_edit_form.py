from astrobin.forms.migratable_gear_item_edit_form import MigratableGearItemEditForm
from astrobin.models import Filter


class FilterEditForm(MigratableGearItemEditForm):
    class Meta:
        model = Filter
        exclude = MigratableGearItemEditForm.Meta.exclude
