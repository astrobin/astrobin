from django import forms
from django.utils.translation import ugettext as __, ugettext_lazy as _
from image_cropping import ImageCropWidget

from astrobin.models import Image, ImageRevision
from astrobin.widgets.select_with_disabled_choices import SelectWithDisabledChoices


class ImageEditRevisionForm(forms.ModelForm):
    mouse_hover_image = forms.ChoiceField(
        required=False,
        label=_("Mouse hover image"),
        help_text=_("Choose what will be displayed when somebody hovers the mouse over this image revision. Please"
                    "note: only revisions with the same width and height as this one can be considered."),
        widget=SelectWithDisabledChoices(attrs={'class': 'form-control'}),
    )

    def __init_mouse_hover_image(self):
        self.fields['mouse_hover_image'].choices = Image.MOUSE_HOVER_CHOICES

        revision = self.instance
        image = revision.image
        other_revisions = image.revisions
        matches_resolution: bool = image.w == revision.w and image.h == revision.h

        def does_not_match_label(matches: bool):
            return "" if matches else " (" + __("pixel resolution does not match") + ")"

        self.fields['mouse_hover_image'].choices = self.fields['mouse_hover_image'].choices + [
            (
                "ORIGINAL" if matches_resolution else "__DISABLED__",
                f'{_("Original image")}{does_not_match_label(matches_resolution)}',
            )
        ]

        for other_revision in other_revisions.all():
            if other_revision.label != self.instance.label:
                matches_resolution: bool = other_revision.w == revision.w and other_revision.h == revision.h
                self.fields['mouse_hover_image'].choices = self.fields['mouse_hover_image'].choices + [
                    (
                        f'REVISION__{other_revision.label}' if matches_resolution else '__DISABLED__',
                        f'{__("Revision")} {other_revision.label}{does_not_match_label(matches_resolution)}',
                    )]

    def __init_loop_video(self):
        if self.instance.video_file.name:
            self.fields['loop_video'] = forms.BooleanField(
                required=False,
                label=_("Loop video"),
                help_text=_("If checked, the video will loop."),
                initial=self.instance.loop_video,
            )

    def __init__(self, **kwargs):
        super(ImageEditRevisionForm, self).__init__(**kwargs)
        self.__init_mouse_hover_image()
        self.__init_loop_video()

    def save(self, commit=True):
        instance = super().save(commit=False)

        if 'loop_video' in self.fields:
            instance.loop_video = self.cleaned_data['loop_video']

        if commit:
            instance.save(keep_deleted=True)

        return instance

    class Meta:
        model = ImageRevision
        fields = ('image_file', 'title', 'description', 'mouse_hover_image', 'square_cropping')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'image_file': ImageCropWidget
        }
