from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.forms.utils import NULL_CHOICE
from astrobin.models import Gear, RetailedGear
from astrobin.utils import retailer_affiliate_limit
from astrobin.utils import uniq, uniq_id_tuple


class ClaimRetailedGearForm(forms.Form):
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
        super(ClaimRetailedGearForm, self).__init__(**kwargs)
        self.user = user
        self.fields['make'].choices = NULL_CHOICE + sorted(
            uniq(Gear.objects.exclude(make=None).exclude(make='').values_list('make', 'make')),
            key=lambda x: x[0].lower())
        self.fields['merge_with'].choices = \
            NULL_CHOICE + \
            uniq_id_tuple(
                RetailedGear.objects.filter(retailer=user).exclude(gear__name=None).values_list('id', 'gear__name'))

    def clean(self):
        cleaned_data = super(ClaimRetailedGearForm, self).clean()

        max_items = retailer_affiliate_limit(self.user)
        current_items = RetailedGear.objects.filter(gear=self.user).count()
        if current_items >= max_items:
            raise forms.ValidationError(
                _("You can't create more than %d claims. Consider upgrading your affiliation!" % max_items))

        already_claimed = set(
            item.id
            for sublist in [x.gear_set.all() for x in RetailedGear.objects.filter(retailer=self.user)]
            for item in sublist)

        if int(cleaned_data['name']) in already_claimed:
            raise forms.ValidationError(_("You have already claimed this product."))

        return self.cleaned_data
