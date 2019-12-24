from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.forms.utils import NULL_CHOICE
from astrobin.utils import uniq
from astrobin.models import Gear, CommercialGear
from astrobin.utils import affiliate_limit


class ClaimCommercialGearForm(forms.Form):
    error_css_class = 'error'

    make = forms.ChoiceField(
        label=_("Make"),
        help_text=_("The make, brand, producer or developer of this product."),
        required=True)

    name = forms.ChoiceField(
        choices=NULL_CHOICE,
        label=_("Name"),
        required=True)

    merge_with = forms.ChoiceField(
        choices=NULL_CHOICE,
        label=_("Merge"),
        help_text=_(
            "Use this field to mark that the item you are claiming really is the same product (or a variation thereof) of something you have claimed before."),
        required=False)

    def __init__(self, user, **kwargs):
        super(ClaimCommercialGearForm, self).__init__(**kwargs)
        self.user = user
        self.fields['make'].choices = NULL_CHOICE + sorted(
            uniq(Gear.objects.exclude(make=None).exclude(make='').values_list('make', 'make')),
            key=lambda x: x[0].lower())
        self.fields['merge_with'].choices = NULL_CHOICE + uniq(
            CommercialGear.objects.filter(producer=user).values_list('id', 'proper_name'))

    def clean(self):
        cleaned_data = super(ClaimCommercialGearForm, self).clean()

        max_items = affiliate_limit(self.user)
        current_items = CommercialGear.objects.filter(producer=self.user).count()
        if current_items >= max_items:
            raise forms.ValidationError(
                _("You can't create more than %d claims. Consider upgrading your affiliation!" % max_items))

        return self.cleaned_data
