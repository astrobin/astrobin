from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.models import Image


class ImageEditWatermarkForm(forms.ModelForm):
    error_css_class = 'error'

    watermark_opacity = forms.IntegerField(
        label=_("Opacity"),
        help_text=_(
            "0 means invisible; 100 means completely opaque. Recommended values are: 10 if the watermark will appear on the dark sky background, 50 if on some bright object."),
        min_value=0,
        max_value=100,
    )

    def __init__(self, user=None, **kwargs):
        super(ImageEditWatermarkForm, self).__init__(**kwargs)

    def clean_watermark_text(self):
        data = self.cleaned_data['watermark_text']
        watermark = self.cleaned_data['watermark']

        if watermark and data == '':
            raise forms.ValidationError(_("If you want to watermark this image, you must specify some text."));

        return data.strip() if data else data

    class Meta:
        model = Image
        fields = ('watermark', 'watermark_text', 'watermark_position', 'watermark_size', 'watermark_opacity',)
