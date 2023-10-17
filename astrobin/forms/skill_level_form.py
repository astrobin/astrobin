from django import forms

from astrobin.forms import UserProfileEditBasicForm


class SkillLevelForm(UserProfileEditBasicForm):
    error_css_class = 'error'

    class Meta(UserProfileEditBasicForm.Meta):
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.fields['real_name'].widget = forms.HiddenInput()
        self.fields['website'].widget = forms.HiddenInput()
        self.fields['job'].widget = forms.HiddenInput()
        self.fields['hobbies'].widget = forms.HiddenInput()
        self.fields['instagram_username'].widget = forms.HiddenInput()
        self.fields['about'].widget = forms.HiddenInput()
