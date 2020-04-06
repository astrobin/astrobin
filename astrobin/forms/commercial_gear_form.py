from django import forms

from astrobin.enums import SubjectType
from astrobin.models import CommercialGear, Image


class CommercialGearForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = CommercialGear
        fields = (
            'proper_make', 'proper_name', 'image', 'tagline', 'link',
            'description')

    def __init__(self, user, **kwargs):
        super(CommercialGearForm, self).__init__(**kwargs)
        self.fields['image'].queryset = Image.objects.filter(user=user, subject_type=SubjectType.GEAR)
