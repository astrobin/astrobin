from django import forms
from django.utils.translation import ugettext_lazy as _


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
        help_text=_(
            "Hint: enter your filters separately! If you enter, for instance, LRGB in one box, you won't be able to add separate acquisition sessions for them."),
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
