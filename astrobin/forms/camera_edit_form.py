from astrobin.forms.migratable_gear_item_edit_form import MigratableGearItemEditForm
from astrobin.models import Camera


class CameraEditForm(MigratableGearItemEditForm):
    class Meta:
        model = Camera
        exclude = MigratableGearItemEditForm.Meta.exclude
