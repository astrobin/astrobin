from django import forms
from django.utils.translation import ugettext_lazy as _

from astrobin.forms.utils import parseKeyValueTags
from astrobin.models import Location, Image
from astrobin_apps_groups.models import Group
from astrobin_apps_images.models import KeyValueTag


class ImageEditBasicForm(forms.ModelForm):
    error_css_class = 'error'

    link = forms.RegexField(
        regex='^(http|https)://',
        required=False,
        label=_("Link"),
        help_text=_("If you're hosting a copy of this image on your website, put the address here."),
        error_messages={'invalid': "The address must start with http:// or https://."},
    )

    link_to_fits = forms.RegexField(
        regex='^(http|https)://',
        required=False,
        label=_("Link to TIFF/FITS"),
        help_text=_(
            "If you want to share the TIFF or FITS file of your image, put a link to the file here. Unfortunately, AstroBin cannot offer to store these files at the moment, so you will have to host them on your personal space."),
        error_messages={'invalid': "The address must start with http:// or https://."},
    )

    groups = forms.MultipleChoiceField(
        required=False,
        label=_("Groups"),
        help_text=_("Submit this image to the selected groups."),
    )

    mouse_hover_image = forms.ChoiceField(
        required=False,
        label=_("Mouse hover image"),
        help_text=_("Choose what will be displayed when somebody hovers the mouse over this image. Please note: only "
                    "revisions with the same width and height of your original image can be considered."),
    )

    keyvaluetags = forms.CharField(
        required=False,
        label=_("Key/value tags"),
        help_text=_("Provide a list of unique key/value pairs to tag this image with. Use the '=' symbol between key "
                    "and value, and provide one pair per line. These tags can be used to sort images by arbitrary "
                    "properties."),
        widget=forms.Textarea(attrs={'rows': 4})
    )

    def __init__(self, *args, **kwargs):
        super(ImageEditBasicForm, self).__init__(*args, **kwargs)

        self.__initLocations()
        self.__initGroups()
        self.__initMouseHoverImage()
        self.__initRevisions()
        self.__initKeyValueTags()

    def __initLocations(self):
        locations = Location.objects.filter(user=self.instance.user.userprofile)
        if locations.count() > 0:
            self.fields['locations'].queryset = locations
        else:
            self.fields.pop('locations')

    def __initGroups(self):
        groups = Group.objects.filter(autosubmission=False, members=self.instance.user)
        if groups.count() > 0:
            self.fields['groups'].choices = [(x.pk, x.name) for x in groups]
            self.fields['groups'].initial = [
                x.pk for x in self.instance.part_of_group_set.filter(
                    autosubmission=False,
                    members=self.instance.user)]
        else:
            self.fields.pop('groups')

    def __initMouseHoverImage(self):
        self.fields['mouse_hover_image'].choices = Image.MOUSE_HOVER_CHOICES

    def __initRevisions(self):
        revisions = self.instance.revisions
        if revisions.count() > 0:
            for revision in revisions.all():
                if revision.w == self.instance.w and revision.h == self.instance.h:
                    self.fields['mouse_hover_image'].choices = self.fields['mouse_hover_image'].choices + [
                        ("REVISION__%s" % revision.label, "%s %s" % (_("Revision"), revision.label))
                    ]

    def __initKeyValueTags(self):
        tags = self.instance.keyvaluetags.all()
        initial = ""
        for tag in tags:
            initial += "%s=%s\r\n" % (tag.key, tag.value)

        self.fields['keyvaluetags'].initial = initial

    def __saveGroups(self, instance):
        if 'groups' in self.cleaned_data:
            existing_groups = instance.part_of_group_set.filter(autosubmission=False)
            new_groups_pks = self.cleaned_data['groups']
            new_groups = [Group.objects.get(pk=int(x)) for x in new_groups_pks]

            for group in existing_groups:
                if group.pk not in [int(x) for x in new_groups_pks]:
                    group.images.remove(self.instance)

            for group in new_groups:
                if group not in existing_groups:
                    group.images.add(self.instance)

    def __saveKeyValueTags(self, instance):
        instance.keyvaluetags.all().delete()

        if 'keyvaluetags' in self.data:
            tags = self.data['keyvaluetags']
            if tags is None:
                return

            for tag in parseKeyValueTags(tags):
                KeyValueTag.objects.create(
                    image=instance,
                    key=tag["key"],
                    value=tag["value"]
                )

    def save(self, commit=True):
        instance = super(ImageEditBasicForm, self).save(commit=False)

        self.__saveGroups(instance)
        self.__saveKeyValueTags(instance)

        return super(ImageEditBasicForm, self).save(commit)

    def clean_link(self):
        return self.cleaned_data['link'].strip()

    def clean_subject_type(self):
        subject_type = self.cleaned_data['subject_type']
        if subject_type is None:
            raise forms.ValidationError(_('This field is required.'))

        return self.cleaned_data['subject_type']

    def clean_keyvaluetags(self):
        try:
            parsed = parseKeyValueTags(self.cleaned_data['keyvaluetags'])
        except ValueError:
            raise forms.ValidationError(_("Unable to parse."))

    def clean_remote_source(self):
        try:
            data_source = self.cleaned_data['data_source']
            remote_source = self.cleaned_data['remote_source']

            if data_source in ['OWN_REMOTE', 'AMATEUR_HOSTING'] and remote_source is None:
                raise forms.ValidationError(_("Please select a remote source if this image was acquired remotely."))
        except KeyError:
            pass

        return self.cleaned_data['remote_source']

    class Meta:
        model = Image
        fields = (
            'image_file',
            'title',
            'link',
            'link_to_fits',
            'acquisition_type',
            'data_source',
            'remote_source',
            'subject_type',
            'solar_system_main_subject',
            'locations',
            'groups',
            'description',
            'keyvaluetags',
            'mouse_hover_image',
            'allow_comments')
