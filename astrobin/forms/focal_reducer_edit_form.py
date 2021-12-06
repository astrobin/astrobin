from astrobin.forms.migratable_gear_item_edit_form import MigratableGearItemEditForm
from astrobin.models import FocalReducer


class FocalReducerEditForm(MigratableGearItemEditForm):
    class Meta:
        model = FocalReducer
        exclude = MigratableGearItemEditForm.Meta.exclude
