from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.forms.utils import NULL_CHOICE
from astrobin.models import RetailedGear
from astrobin.utils import uniq_id_tuple


class MergeRetailedGearForm(forms.Form):
    error_css_class = 'error'

    merge_with = forms.ChoiceField(
        choices=NULL_CHOICE,
        label=_("Merge"),
        help_text=_(
            "Use this field to mark that the item you are merging really is the same product (or a variation thereof) of something you have claimed before."),
        required=False)

    def __init__(self, user, **kwargs):
        super(MergeRetailedGearForm, self).__init__(**kwargs)
        self.fields['merge_with'].choices = \
            NULL_CHOICE + \
            uniq_id_tuple(
                RetailedGear.objects.filter(retailer=user).exclude(gear__name=None).values_list('id', 'gear__name'))
