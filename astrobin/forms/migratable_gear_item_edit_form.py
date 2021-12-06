from django import forms


class MigratableGearItemEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        abstract = True
        exclude = (
            'make',
            'name',
            'migration_flag_moderator_lock',
            'migration_flag_moderator_lock_timestamp',
        )
