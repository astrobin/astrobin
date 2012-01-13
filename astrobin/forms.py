from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _

from haystack.forms import SearchForm
from haystack.query import SearchQuerySet, EmptySearchQuerySet

from models import *

from search_indexes import xapian_escape

import string
import unicodedata

from management import NOTICE_TYPES

class ImageUploadForm(forms.Form):
    file = forms.ImageField()


class ImageEditPresolveForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('presolve_information',)
        widgets = {
            'presolve_information': forms.RadioSelect(choices = Image.SOLVE_CHOICES),
        }


class ImageEditBasicForm(forms.ModelForm):
    error_css_class = 'error'

    link = forms.RegexField(
        regex = '^(http|https)://',
        required = False,
        help_text = _("If you're hosting a copy of this image on your website, put the address here."),
        error_messages = {'invalid': "The address must start with http:// or https://."},
    )
    subjects = forms.CharField(
        required = False,
        help_text=_("If possible, use catalog names (e.g. M101, or NGC224 or IC1370)."),
    )
    locations = forms.CharField(
        required = False,
        help_text=_("The places from which you have taken this image."),
    )

    def __init__(self, user=None, **kwargs):
        super(ImageEditBasicForm, self).__init__(**kwargs)
        self.fields['link'].label = _("Link")
        self.fields['subjects'].label = _("Subjects")
        self.fields['locations'].label = _("Locations")

    def clean_link(self):
        return self.cleaned_data['link'].strip()

    def clean(self):
        subjects = self.data['as_values_subjects'].strip()
        solar_system = self.cleaned_data['solar_system_main_subject']

        if solar_system is None and (len(subjects) == 0 or subjects[0] == ''):
            raise forms.ValidationError(_("Please enter either some subjects or a main solar system subject."));

        return self.cleaned_data

    class Meta:
        model = Image
        fields = ('title', 'link', 'subjects', 'solar_system_main_subject', 'locations', 'description')


class ImageEditWatermarkForm(forms.ModelForm):
    error_css_class = 'error'

    watermark_opacity = forms.IntegerField(
        label = _("Opacity"),
        help_text = _("0 means invisible; 100 means completely opaque. Recommended values are: 10 if the watermark will appear on the dark sky background, 50 if on some bright object."),
        min_value = 0,
        max_value = 100,
    )

    def __init__(self, user=None, **kwargs):
        super(ImageEditWatermarkForm, self).__init__(**kwargs)

    def clean_watermark_text(self):
        data = self.cleaned_data['watermark_text']
        watermark = self.cleaned_data['watermark']

        if watermark and data == '':
            raise forms.ValidationError(_("If you want to watermark this image, you must specify some text."));

        return data.strip()

    class Meta:
        model = Image
        fields = ('watermark', 'watermark_text', 'watermark_position', 'watermark_opacity',)


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

        self.fields['imaging_telescopes'].label = _("Imaging telescopes or lenses")
        self.fields['guiding_telescopes'].label = _("Guiding telescopes or lenses")
        self.fields['mounts'].label = _("Mounts")
        self.fields['imaging_cameras'].label = _("Imaging cameras")
        self.fields['guiding_cameras'].label = _("Guiding cameras")
        self.fields['focal_reducers'].label = _("Focal reducers")
        self.fields['software'].label = _("Software")
        self.fields['filters'].label = _("Filters")
        self.fields['accessories'].label = _("Accessories")

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
    error_css_class = 'error'

    website = forms.RegexField(
        regex = '^(http|https)://',
        required = False,
        help_text = _("If you have a personal website, put the address here."),
        error_messages = {'invalid': "The address must start with http:// or https://."},
    )

    locations = forms.CharField(
        max_length = 256,
        required = False,
        help_text = _("These are the cities from which you usually image."),
    )

    class Meta:
        model = UserProfile
        fields = ('website', 'job', 'hobbies', 'timezone', 'locations', 'about')

    def __init__(self, user=None, **kwargs):
        super(UserProfileEditBasicForm, self).__init__(**kwargs)
        self.fields['locations'].label = _("Locations")
        self.fields['website'].label = _("Website")


class UserProfileEditGearForm(forms.Form):
    telescopes = forms.CharField(
        max_length=256,
        help_text=_("All the telescopes and lenses you own, including the ones you use for guiding, go here."),
        required=False)

    mounts = forms.CharField(
        max_length=256,
        required=False)

    cameras = forms.CharField(
        max_length=256,
        help_text=_("Your DSLRs, CCDs, planetary cameras and guiding cameras go here."),
        required=False)

    focal_reducers = forms.CharField(
        max_length=256,
        required=False)

    software = forms.CharField(
        max_length=256,
        required=False)

    filters = forms.CharField(
        max_length=256,
        help_text=_("Hint: enter your filters separately! If you enter, for instance, LRGB in one box, you won't be able to add separate acquisition sessions for them."),
        required=False)

    accessories = forms.CharField(
        max_length=256,
        required=False)

    def __init__(self, user=None, **kwargs):
        super(UserProfileEditGearForm, self).__init__(**kwargs)
        self.fields['telescopes'].label = _("Telescopes and lenses")
        self.fields['mounts'].label = _("Mounts")
        self.fields['cameras'].label = _("Cameras")
        self.fields['focal_reducers'].label = _("Focal reducers")
        self.fields['software'].label = _("Software")
        self.fields['filters'].label = _("Filters")
        self.fields['accessories'].label = _("Accessories")


class UserProfileEditPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('language',)

    def __init__(self, user=None, **kwargs):
        super(UserProfileEditPreferencesForm, self).__init__(**kwargs)
        for notice_type in NOTICE_TYPES:
            if notice_type[3] == 2:
                self.fields[notice_type[0]] = forms.BooleanField(
                    label=notice_type[1],
                    required=False
                )


class PrivateMessageForm(forms.Form):
    subject = forms.CharField(max_length=255, required=False)
    body = forms.CharField(widget=forms.Textarea, max_length=4096, required=False)


class BringToAttentionForm(forms.Form):
    user = forms.CharField(max_length=64, required=False)

    def __init__(self, user=None, **kwargs):
        super(BringToAttentionForm, self).__init__(**kwargs)
        self.fields['user'].label = _("User")


class ImageRevisionUploadForm(forms.Form):
    file = forms.ImageField()


class AdvancedSearchForm(SearchForm):
    imaging_telescopes = forms.CharField(
        required = False
    )
    imaging_cameras = forms.CharField(
        required = False
    )
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
        self.fields['q'].help_text = _("Search for astronomical objects, telescopes or lenses, cameras, filters...")

        self.fields['imaging_telescopes'].label = _("Imaging telescopes or lenses")
        self.fields['imaging_cameras'].label = _("Imaging cameras")
        self.fields['start_date'].label = _("Acquired after")
        self.fields['end_date'].label = _("Acquired before")
        self.fields['integration_min'].label = _("Min. integration")
        self.fields['integration_max'].label = _("Max. integration")
        self.fields['moon_phase_min'].label = _("Min. Moon phase %")
        self.fields['moon_phase_max'].label = _("Max. Moon phase %")

    def search(self):
        sqs = EmptySearchQuerySet()

        if self.is_valid():
            q = xapian_escape(self.cleaned_data['q']).replace(' ', '')
            self.cleaned_data['q'] = q

            if self.cleaned_data['q'] == '':
                sqs = SearchQuerySet().all().models(Image)
                if self.load_all:
                    sqs = sqs.load_all()
            else:
                sqs = super(AdvancedSearchForm, self).search().models(Image)

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


class LocationEditForm(forms.ModelForm):
    latitude = forms.FloatField(
        required=False,
        help_text=_("For example: +12.44"))
    longitude = forms.FloatField(
        required=False,
        help_text=_("For example: -51.25"))

    def __init__(self, *args, **kwargs):
        super(LocationEditForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            self.fields['name'].widget.attrs['readonly'] = True

    class Meta:
        model = Location
        fields = (
            'name',
            'latitude',
            'longitude',
            'altitude',
        )


class SolarSystem_AcquisitionForm(forms.ModelForm):
    error_css_class = 'error'

    date = forms.DateField(
        required=False,
        input_formats = ['%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class':'datepickerclass'}),
        help_text=_("Please use the following format: yyyy-mm-dd"))

    def clean_seeing(self):
        data = self.cleaned_data['seeing']
        if data and data not in range(1, 5):
            raise forms.ValidationError(_("Please enter a value between 1 and 5."))

    def clean_transparency(self):
        data = self.cleaned_data['transparency']
        if data and data not in range(1, 10):
            raise forms.ValidationError(_("Please enter a value between 1 and 10."))

    class Meta:
        model = SolarSystem_Acquisition
        fields = (
            'date',
            'time',
            'frames',
            'fps',
            'focal_length',
            'cmi',
            'cmii',
            'cmiii',
            'seeing',
            'transparency',
        )
        widgets = {
            'date': forms.TextInput(attrs={'class': 'datepickerclass'}),
            'time': forms.TextInput(attrs={'class': 'timepickerclass'}),
        }


class DeepSky_AcquisitionForm(forms.ModelForm):
    error_css_class = 'error'

    date = forms.DateField(
        required=False,
        input_formats = ['%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class':'datepickerclass'}),
        help_text=_("Please use the following format: yyyy-mm-dd"))

    class Meta:
        model = DeepSky_Acquisition

    def __init__(self, user=None, **kwargs):
        queryset = None
        try:
            queryset = kwargs.pop('queryset')
        except KeyError:
            pass

        super(DeepSky_AcquisitionForm, self).__init__(**kwargs)
        self.fields['date'].label = _("Date")
        if queryset:
            self.fields['filter'].queryset = queryset

    def save(self, force_insert=False, force_update=False, commit=True):
        m = super(DeepSky_AcquisitionForm, self).save(commit=False)
        m.advanced = True
        if commit:
            m.save()
        return m


class DeepSky_AcquisitionBasicForm(forms.ModelForm):
    error_css_class = 'error'

    date = forms.DateField(
        required=False,
        input_formats = ['%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class':'datepickerclass'}),
        help_text=_("Please use the following format: yyyy-mm-dd"))

    class Meta:
        model = DeepSky_Acquisition
        fields = ('date', 'number', 'duration',)
        widgets = {
            'date': forms.TextInput(attrs={'class': 'datepickerclass'}),
        }


class DefaultImageLicenseForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('default_license',)


class ImageLicenseForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('license',)


