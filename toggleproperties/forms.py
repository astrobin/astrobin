from django import forms
from models import ToggleProperty

class DeleteTogglePropertyForm(forms.ModelForm):
    """
    base class for deleting ToggleProperty instance

    you may extend this form to provide additional
    validation rules (checkboxes, captcha, etc...)
    """

    class Meta:
        model = ToggleProperty
        fields = ('id',)

    def save(self, commit=True):
        """
        Simply deletes bound instance and returns instance.
        If commit is set to False, does nothing.
        """

        if commit:
            self.instance.delete()
        return self.instance

