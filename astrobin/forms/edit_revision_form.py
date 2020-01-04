from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.models import Image, ImageRevision


class ImageEditRevisionForm(forms.ModelForm):
    mouse_hover_image = forms.ChoiceField(
        required=False,
        label=_("Mouse hover image"),
        help_text=_("Choose what will be displayed when somebody hovers the mouse over this image revision. Please"
                    "note: only revisions with the same width and height as this one can be considered."),
    )

    def __init__(self, **kwargs):
        super(ImageEditRevisionForm, self).__init__(**kwargs)

        self.fields['mouse_hover_image'].choices = Image.MOUSE_HOVER_CHOICES

        revisions = self.instance.image.revisions
        if revisions.count() > 0:
            for revision in revisions.all():
                if revision.label != self.instance.label \
                        and revision.w == self.instance.w \
                        and revision.h == self.instance.h:
                    self.fields['mouse_hover_image'].choices = self.fields['mouse_hover_image'].choices + [
                        ("REVISION__%s" % revision.label, "%s %s" % (_("Revision"), revision.label))
                    ]

        if self.instance.w == self.instance.image.w and self.instance.h == self.instance.image.h:
            self.fields['mouse_hover_image'].choices = self.fields['mouse_hover_image'].choices + [
                ("ORIGINAL", _("Original image"))
            ]

    class Meta:
        model = ImageRevision
        fields = ('description', 'mouse_hover_image')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
