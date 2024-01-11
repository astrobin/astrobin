from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.fields import GearItemChoiceField
from astrobin.models import Image
from astrobin.services.gear_service import GearService


class ImageEditGearForm(forms.ModelForm):
    imaging_telescopes = GearItemChoiceField(
        None,
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                'multiple': True
            }
        )
    )
    imaging_cameras = GearItemChoiceField(
        None,
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                'multiple': True
            }
        )
    )

    guiding_telescopes = GearItemChoiceField(
        None,
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                'multiple': True
            }
        )
    )
    guiding_cameras = GearItemChoiceField(
        None,
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                'multiple': True
            }
        )
    )
    mounts = GearItemChoiceField(
        None,
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                'multiple': True
            }
        )
    )
    filters = GearItemChoiceField(
        None,
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                'multiple': True
            }
        )
    )
    accessories = GearItemChoiceField(
        None,
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                'multiple': True
            }
        )
    )
    software = GearItemChoiceField(
        None,
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                'multiple': True
            }
        )
    )
    focal_reducers = GearItemChoiceField(
        None,
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                'multiple': True
            }
        )
    )

    def __init_fields__(self, user):
        for field in GearService.get_legacy_gear_usage_classes():
            self.fields[field].user = user

    def __init__(self, user=None, **kwargs):
        super(ImageEditGearForm, self).__init__(**kwargs)
        profile = user.userprofile
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

        self.__init_fields__(user)

    class Meta:
        model = Image
        fields = GearService.get_legacy_gear_usage_classes()
