from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.models import CommercialGear
from astrobin.utils import uniq


class MergeCommercialGearForm(forms.Form):
    error_css_class = 'error'

    merge_with = forms.ChoiceField(
        choices=[('', '---------')],
        label=_("Merge"),
        help_text=_(
            "Use this field to mark that the item you are merging really is the same product (or a variation thereof) of something you have claimed before."),
        required=False)

    def __init__(self, user, **kwargs):
        super(MergeCommercialGearForm, self).__init__(**kwargs)
        self.fields['merge_with'].choices = [('', '---------')] + uniq(
            CommercialGear.objects.filter(producer=user).values_list('id', 'proper_name'))
