from django import forms
from django.db import models
from django.utils.translation import ugettext as _

from haystack.forms import SearchForm

from models import Image
from models import UserProfile


class ImageUploadForm(forms.Form):
    file = forms.ImageField()


class ImageEditBasicForm(forms.Form):
    title = forms.CharField(max_length=64)
    subjects = forms.CharField(required=False, help_text="<noscript>*</noscript>")
    locations = forms.CharField(required=False, help_text="<noscript>*</noscript>")
    description = forms.CharField(widget=forms.Textarea, required=False)


class ImageEditGearForm(forms.ModelForm):
    def __init__(self, user=None, **kwargs):
        super(ImageEditGearForm, self).__init__(**kwargs)
        profile = UserProfile.objects.get(user=user)
        telescopes = profile.telescopes.all()
        self.fields['imaging_telescopes'].queryset = telescopes
        self.fields['guiding_telescopes'].queryset = telescopes
        cameras = profile.cameras.all()
        self.fields['imaging_cameras'].queryset = cameras
        self.fields['guiding_cameras'].queryset = cameras
        for attr in ('mounts',
                     'focal_reducers',
                     'software',
                     'filters',
                     'accessories',
                    ):
            self.fields[attr].queryset = getattr(profile, attr).all()

    class Meta:
        model = Image
        fields = ('imaging_telescopes',
                  'guiding_telescopes',
                  'mounts',
                  'imaging_cameras',
                  'guiding_cameras',
                  'focal_reducers',
                  'software',
                  'filters',
                  'accessories',
                 )


class UserProfileEditBasicForm(forms.ModelForm):
    locations = forms.CharField(max_length=64, required=False, help_text="<noscript>*</noscript>")
    class Meta:
        model = UserProfile
        fields = ('website', 'job', 'hobbies')


class UserProfileEditGearForm(forms.Form):
    telescopes = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    mounts = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    cameras = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    focal_reducers = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    software = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    filters = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")
    accessories = forms.CharField(max_length=256, help_text="<noscript>*</noscript>")


class PrivateMessageForm(forms.Form):
    subject = forms.CharField(max_length=255, required=False)
    body = forms.CharField(widget=forms.Textarea, max_length=4096, required=False)


class BringToAttentionForm(forms.Form):
    user = forms.CharField(max_length=64, required=False)


class ImageRevisionUploadForm(forms.Form):
    file = forms.ImageField()


class AdvancedSearchForm(SearchForm):
    start_date = forms.DateField(
        required=False,
        widget=forms.TextInput(attrs={'class':'datepickerclass'}),
        help_text=_("Please use the following format: yyyy-mm-dd"))
    end_date = forms.DateField(
        required=False,
        widget=forms.TextInput(attrs={'class':'datepickerclass'}),
        help_text=_("Please use the following format: yyyy-mm-dd"))
    integration_min = forms.FloatField(
        required=False,
        help_text=_("Express value in hours"))
    integration_max = forms.FloatField(
        required=False,
        help_text=_("Express value in hours"))
    moon_phase_min = forms.FloatField(
        required=False,
        help_text="0-100")
    moon_phase_max = forms.FloatField(
        required=False,
        help_text="0-100")

    def __init__(self, data=None, **kwargs):
        super(AdvancedSearchForm, self).__init__(data, **kwargs)
        self.fields['start_date'].label = _("Min. upload date")
        self.fields['end_date'].label = _("Max. upload date")
        self.fields['integration_min'].label = _("Min. integration")
        self.fields['integration_max'].label = _("Max. integration")
        self.fields['moon_phase_min'].label = _("Min. Moon phase %")
        self.fields['moon_phase_max'].label = _("Max. Moon phase %")

    def search(self):
        # First, store the SearchQuerySet received from other processing.
        sqs = super(AdvancedSearchForm, self).search()
 
        if self.is_valid():
            if self.cleaned_data['start_date']:
                sqs = sqs.filter(last_acquisition_date__gte=self.cleaned_data['start_date'])

            if self.cleaned_data['end_date']:
                sqs = sqs.filter(first_acquisition_date__lte=self.cleaned_data['end_date'])

            if self.cleaned_data['integration_min']:
                sqs = sqs.filter(integration__gte=int(self.cleaned_data['integration_min'] * 3600))

            if self.cleaned_data['integration_max']:
                sqs = sqs.filter(integration__lte=int(self.cleaned_data['integration_max'] * 3600))

            if self.cleaned_data['moon_phase_min']:
                sqs = sqs.filter(moon_phase__gte=self.cleaned_data['moon_phase_min'])

            if self.cleaned_data['moon_phase_max']:
                sqs = sqs.filter(moon_phase__lte=self.cleaned_data['moon_phase_max'])

        return sqs

