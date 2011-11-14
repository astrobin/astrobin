from django import forms
from django.db import models
from django.utils.translation import ugettext as _

from haystack.forms import SearchForm
from haystack.query import SearchQuerySet, EmptySearchQuerySet

from models import Image
from models import UserProfile
from models import Location
from models import DeepSky_Acquisition

from search_indexes import xapian_escape

import string

class ImageUploadForm(forms.Form):
    file = forms.ImageField()


class ImageEditPresolveForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('focal_length', 'pixel_size', 'binning', 'scaling',)


class ImageEditBasicForm(forms.Form):
    title = forms.CharField(max_length=64)
    subjects = forms.CharField(required=False, help_text="<noscript>*</noscript>" + _("If possible, use catalog names (e.g. M101, or NGC224 or IC1370)."))
    locations = forms.CharField(required=False, help_text="<noscript>*</noscript>" + _("The places from which you have taken this image."))
    description = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, user=None, **kwargs):
        super(ImageEditBasicForm, self).__init__(**kwargs)
        self.fields['title'].label = _("Title")
        self.fields['subjects'].label = _("Subjects")
        self.fields['locations'].label = _("Locations")
        self.fields['description'].label = _("Description")


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

        self.fields['imaging_telescopes'].label = _("Imaging telescopes")
        self.fields['guiding_telescopes'].label = _("Guiding telescopes")
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
    locations = forms.CharField(max_length=64, required=False, help_text="<noscript>*</noscript>")

    class Meta:
        model = UserProfile
        fields = ('website', 'job', 'hobbies', 'timezone',)

    def __init__(self, user=None, **kwargs):
        super(UserProfileEditBasicForm, self).__init__(**kwargs)
        self.fields['locations'].label = _("Locations")


class UserProfileEditGearForm(forms.Form):
    telescopes = forms.CharField(
        max_length=256,
        help_text="<noscript>*</noscript>" + _("All the telescopes you own, including the ones you use for guiding, go here."),
        required=False)

    mounts = forms.CharField(
        max_length=256,
        help_text="<noscript>*</noscript>",
        required=False)

    cameras = forms.CharField(
        max_length=256,
        help_text="<noscript>*</noscript>" + _("Your DSLRs, CCDs, planetary cameras and guiding cameras go here."),
        required=False)

    focal_reducers = forms.CharField(
        max_length=256,
        help_text="<noscript>*</noscript>",
        required=False)

    software = forms.CharField(
        max_length=256,
        help_text="<noscript>*</noscript>",
        required=False)

    filters = forms.CharField(
        max_length=256,
        help_text="<noscript>*</noscript>" + _("Hint: enter your filters separately! If you enter, for instance, LRGB in one box, you won't be able to add separate acquisition sessions for them."),
        required=False)

    accessories = forms.CharField(
        max_length=256,
        help_text="<noscript>*</noscript>",
        required=False)

    def __init__(self, user=None, **kwargs):
        super(UserProfileEditGearForm, self).__init__(**kwargs)
        self.fields['telescopes'].label = _("Telescopes")
        self.fields['mounts'].label = _("Mounts")
        self.fields['cameras'].label = _("Cameras")
        self.fields['focal_reducers'].label = _("Focal reducers")
        self.fields['software'].label = _("Software")
        self.fields['filters'].label = _("Filters")
        self.fields['accessories'].label = _("Accessories")


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
        self.fields['q'].help_text = _("Search for astronomical objects, telescopes, cameras, filters...")

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
                sqs = SearchQuerySet().all()
                if self.load_all:
                    sqs = sqs.load_all()
            else:
                sqs = super(AdvancedSearchForm, self).search()


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


class DeepSky_AcquisitionForm(forms.ModelForm):
    date = forms.DateField(
        required=False,
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
    date = forms.DateField(
        required=False,
        widget=forms.TextInput(attrs={'class':'datepickerclass'}),
        help_text=_("Please use the following format: yyyy-mm-dd"))

    class Meta:
        model = DeepSky_Acquisition
        fields = ('date', 'number', 'duration',)

    def __init__(self, user=None, **kwargs):
        super(DeepSky_AcquisitionBasicForm, self).__init__(**kwargs)
        self.fields['date'].label = _("Date")

