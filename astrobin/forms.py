# Python
import datetime

# Django
from django.utils.translation import ugettext_lazy as _

# AstroBin apps
from astrobin_apps_groups.models import Group
# This app
from models import *
from utils import affiliate_limit, retailer_affiliate_limit


# Third party apps


def uniq(seq):
    # Not order preserving
    keys = {}
    for e in seq:
        keys[e] = 1
    return keys.keys()


def uniq_id_tuple(seq):
    seen = set()
    ret = []
    for e in seq:
        id = e[0]
        if id not in seen:
            seen.add(id)
            ret.append(e)
    return ret


class ImageFlagThumbsForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ()


class ImagePromoteForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ()


class ImageDemoteForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ()


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('image_file',)


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

    def __init__(self, **kwargs):
        super(ImageEditBasicForm, self).__init__(**kwargs)

        locations = Location.objects.filter(user=self.instance.user.userprofile)
        if locations.count() > 0:
            self.fields['locations'].queryset = locations
        else:
            self.fields.pop('locations')

        groups = Group.objects.filter(autosubmission=False, members=self.instance.user)
        if groups.count() > 0:
            self.fields['groups'].choices = [(x.pk, x.name) for x in groups]
            self.fields['groups'].initial = [
                x.pk for x in self.instance.part_of_group_set.filter(
                    autosubmission=False,
                    members=self.instance.user)]
        else:
            self.fields.pop('groups')

    def save(self, commit=True):
        instance = super(ImageEditBasicForm, self).save(commit=False)

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

        return super(ImageEditBasicForm, self).save(commit)

    def clean_link(self):
        return self.cleaned_data['link'].strip()

    def clean_subject_type(self):
        subject_type = self.cleaned_data['subject_type']
        if subject_type == 0:
            raise forms.ValidationError(_('This field is required.'))

        return self.cleaned_data['subject_type']

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
            'title', 'link', 'link_to_fits', 'acquisition_type', 'data_source', 'remote_source', 'subject_type',
            'solar_system_main_subject', 'locations', 'groups', 'description',
            'allow_comments')


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

        return data.strip()

    class Meta:
        model = Image
        fields = ('watermark', 'watermark_text', 'watermark_position', 'watermark_size', 'watermark_opacity',)


class ImageEditGearForm(forms.ModelForm):
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

    class Meta:
        model = Image
        fields = ('imaging_telescopes',
                  'guiding_telescopes',
                  'mounts',
                  'imaging_cameras',
                  'guiding_cameras',
                  'focal_reducers',
                  'software',
                  'filters',
                  'accessories',
                  )


class ImageEditRevisionForm(forms.ModelForm):
    class Meta:
        model = ImageRevision
        fields = ('description',)
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class UserProfileEditBasicForm(forms.ModelForm):
    error_css_class = 'error'

    website = forms.RegexField(
        regex='^(http|https)://',
        required=False,
        help_text=_("If you have a personal website, put the address here."),
        error_messages={'invalid': "The address must start with http:// or https://."},
    )

    class Meta:
        model = UserProfile
        fields = ('real_name', 'website', 'job', 'hobbies', 'timezone', 'about')

    def __init__(self, **kwargs):
        super(UserProfileEditBasicForm, self).__init__(**kwargs)
        self.fields['website'].label = _("Website")


class UserProfileEditCommercialForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = UserProfile
        fields = ('company_name', 'company_description', 'company_website',)


class UserProfileEditRetailerForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = UserProfile
        fields = (
            'retailer_country',
        )


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


class UserProfileEditPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'language',
            'default_frontpage_section',
            'default_gallery_sorting',
            'exclude_from_competitions',
            'receive_forum_emails',
            'receive_important_communications',
            'receive_newsletter',
            'receive_marketing_and_commercial_material'
        ]


class PrivateMessageForm(forms.Form):
    subject = forms.CharField(max_length=255, required=False)
    body = forms.CharField(widget=forms.Textarea, max_length=4096, required=False)


class BringToAttentionForm(forms.Form):
    users = forms.CharField(max_length=64, required=False)

    def __init__(self, user=None, **kwargs):
        super(BringToAttentionForm, self).__init__(**kwargs)
        self.fields['users'].label = _("Users")


class ImageRevisionUploadForm(forms.ModelForm):
    class Meta:
        model = ImageRevision
        fields = ('image_file', 'description',)
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class LocationEditForm(forms.ModelForm):
    error_css_class = 'error'

    lat_deg = forms.IntegerField(
        label=_("Latitude (degrees)"),
        help_text="(0-90)",
        max_value=90,
        min_value=0)
    lat_min = forms.IntegerField(
        label=_("Latitude (minutes)"),
        help_text="(0-60)",
        max_value=60,
        min_value=0,
        required=False)
    lat_sec = forms.IntegerField(
        label=_("Latitude (seconds)"),
        help_text="(0-60)",
        max_value=60,
        min_value=0,
        required=False)

    lon_deg = forms.IntegerField(
        label=_("Longitude (degrees)"),
        help_text="(0-180)",
        max_value=180,
        min_value=0)
    lon_min = forms.IntegerField(
        label=_("Longitude (minutes)"),
        help_text="(0-60)",
        max_value=60,
        min_value=0,
        required=False)
    lon_sec = forms.IntegerField(
        label=_("Longitude (seconds)"),
        help_text="(0-60)",
        max_value=60,
        min_value=0,
        required=False)

    def __init__(self, **kwargs):
        super(LocationEditForm, self).__init__(**kwargs)
        self.fields['country'].choices = sorted(COUNTRIES, key=lambda c: c[1])

    class Meta:
        model = Location
        exclude = []


class SolarSystem_AcquisitionForm(forms.ModelForm):
    error_css_class = 'error'

    date = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'datepickerclass'}),
        help_text=_("Please use the following format: yyyy-mm-dd"),
        label=_("Date"),
    )

    def clean_seeing(self):
        data = self.cleaned_data['seeing']
        if data and data not in range(1, 6):
            raise forms.ValidationError(_("Please enter a value between 1 and 5."))

        return data

    def clean_transparency(self):
        data = self.cleaned_data['transparency']
        if data and data not in range(1, 11):
            raise forms.ValidationError(_("Please enter a value between 1 and 10."))

        return data

    class Meta:
        model = SolarSystem_Acquisition
        fields = (
            'date',
            'time',
            'frames',
            'fps',
            'focal_length',
            'cmi',
            'cmii',
            'cmiii',
            'seeing',
            'transparency',
        )
        widgets = {
            'date': forms.TextInput(attrs={'class': 'datepickerclass'}),
            'time': forms.TextInput(attrs={'class': 'timepickerclass'}),
        }


class DeepSky_AcquisitionForm(forms.ModelForm):
    error_css_class = 'error'

    date = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'datepickerclass'}),
        help_text=_("Please use the following format: yyyy-mm-dd"),
        label=_("Date"),
    )

    class Meta:
        model = DeepSky_Acquisition
        exclude = []

    def __init__(self, user=None, **kwargs):
        queryset = None
        try:
            queryset = kwargs.pop('queryset')
        except KeyError:
            pass

        super(DeepSky_AcquisitionForm, self).__init__(**kwargs)
        if queryset:
            self.fields['filter'].queryset = queryset
        self.fields['number'].required = True
        self.fields['duration'].required = True

    def save(self, force_insert=False, force_update=False, commit=True):
        m = super(DeepSky_AcquisitionForm, self).save(commit=False)
        m.advanced = True
        if commit:
            m.save()
        return m

    def clean_date(self):
        date = self.cleaned_data['date']
        if date and date > datetime.today().date():
            raise forms.ValidationError(_("The date cannot be in the future."))
        return date


class DeepSky_AcquisitionBasicForm(forms.ModelForm):
    error_css_class = 'error'

    date = forms.DateField(
        required=False,
        input_formats=['%Y-%m-%d'],
        widget=forms.TextInput(attrs={'class': 'datepickerclass'}),
        help_text=_("Please use the following format: yyyy-mm-dd"),
        label=_("Date"),
    )

    def clean_date(self):
        date = self.cleaned_data['date']
        if date and date > datetime.today().date():
            raise forms.ValidationError(_("The date cannot be in the future."))
        return date

    class Meta:
        model = DeepSky_Acquisition
        fields = ('date', 'number', 'duration',)
        widgets = {
            'date': forms.TextInput(attrs={'class': 'datepickerclass'}),
        }


class DefaultImageLicenseForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('default_license',)


class ImageLicenseForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('license',)


class TelescopeEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Telescope
        exclude = ('make', 'name', 'retailed')


class MountEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Mount
        exclude = ('make', 'name', 'retailed')


class CameraEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Camera
        exclude = ('make', 'name', 'retailed')


class FocalReducerEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = FocalReducer
        exclude = ('make', 'name', 'retailed')


class SoftwareEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Software
        exclude = ('make', 'name', 'retailed')


class FilterEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Filter
        exclude = ('make', 'name', 'retailed')


class AccessoryEditForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Accessory
        exclude = ('make', 'name', 'retailed')


class TelescopeEditNewForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Telescope
        fields = ('make', 'name')
        widgets = {
            'make': forms.TextInput(attrs={'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }


class MountEditNewForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Mount
        fields = ('make', 'name')
        widgets = {
            'make': forms.TextInput(attrs={'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }


class CameraEditNewForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Camera
        fields = ('make', 'name')
        widgets = {
            'make': forms.TextInput(attrs={'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }


class FocalReducerEditNewForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = FocalReducer
        fields = ('make', 'name')
        widgets = {
            'make': forms.TextInput(attrs={'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }


class SoftwareEditNewForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Software
        fields = ('make', 'name')
        widgets = {
            'make': forms.TextInput(attrs={'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }


class FilterEditNewForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Filter
        fields = ('make', 'name')
        widgets = {
            'make': forms.TextInput(attrs={'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }


class AccessoryEditNewForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Accessory
        fields = ('make', 'name')
        widgets = {
            'make': forms.TextInput(attrs={'autocomplete': 'off'}),
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
        }


class CopyGearForm(forms.Form):
    image = forms.ModelChoiceField(
        queryset=None,
    )

    def __init__(self, user, **kwargs):
        super(CopyGearForm, self).__init__(**kwargs)
        self.fields['image'].queryset = Image.objects_including_wip.filter(user=user)


class AppApiKeyRequestForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = AppApiKeyRequest
        exclude = []


class GearUserInfoForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = GearUserInfo
        exclude = []


class ModeratorGearFixForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Gear
        fields = ('make', 'name',)

    def __init__(self, **kwargs):
        super(ModeratorGearFixForm, self).__init__(**kwargs)
        self.widgets['make'] = forms.TextInput(attrs={
            'data-provide': 'typeahead',
            'data-source': simplejson.dumps(
                uniq([x.make for x in Gear.objects.exclude(make=None).exclude(make='')])),
            'autocomplete': 'off',
        })

    def clean_make(self):
        return self.cleaned_data['make'].strip()

    def clean_name(self):
        return self.cleaned_data['name'].strip()

    def save(self, force_insert=False, force_update=False, commit=True):
        instance = getattr(self, 'instance', None)
        old_make = Gear.objects.get(id=instance.id).make
        old_name = Gear.objects.get(id=instance.id).name

        m = super(ModeratorGearFixForm, self).save(commit=False)

        # Update the time
        m.moderator_fixed = datetime.datetime.now()

        if commit:
            m.save()

        return m


class ClaimCommercialGearForm(forms.Form):
    error_css_class = 'error'

    make = forms.ChoiceField(
        label=_("Make"),
        help_text=_("The make, brand, producer or developer of this product."),
        required=True)

    name = forms.ChoiceField(
        choices=[('', '---------')],
        label=_("Name"),
        required=True)

    merge_with = forms.ChoiceField(
        choices=[('', '---------')],
        label=_("Merge"),
        help_text=_(
            "Use this field to mark that the item you are claiming really is the same product (or a variation thereof) of something you have claimed before."),
        required=False)

    def __init__(self, user, **kwargs):
        super(ClaimCommercialGearForm, self).__init__(**kwargs)
        self.user = user
        self.fields['make'].choices = [('', '---------')] + sorted(
            uniq(Gear.objects.exclude(make=None).exclude(make='').values_list('make', 'make')),
            key=lambda x: x[0].lower())
        self.fields['merge_with'].choices = [('', '---------')] + uniq(
            CommercialGear.objects.filter(producer=user).values_list('id', 'proper_name'))

    def clean(self):
        cleaned_data = super(ClaimCommercialGearForm, self).clean()

        max_items = affiliate_limit(self.user)
        current_items = CommercialGear.objects.filter(producer=self.user).count()
        if current_items >= max_items:
            raise forms.ValidationError(
                _("You can't create more than %d claims. Consider upgrading your affiliation!" % max_items))

        return self.cleaned_data


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


class CommercialGearForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = CommercialGear
        fields = (
            'proper_make', 'proper_name', 'image', 'tagline', 'link',
            'description')

    def __init__(self, user, **kwargs):
        super(CommercialGearForm, self).__init__(**kwargs)
        self.fields['image'].queryset = Image.objects.filter(user=user, subject_type=500)


class ClaimRetailedGearForm(forms.Form):
    error_css_class = 'error'

    make = forms.ChoiceField(
        label=_("Make"),
        help_text=_("The make, brand, producer or developer of this product."),
        required=True)

    name = forms.ChoiceField(
        choices=[('', '---------')],
        label=_("Name"),
        required=True)

    merge_with = forms.ChoiceField(
        choices=[('', '---------')],
        label=_("Merge"),
        help_text=_(
            "Use this field to mark that the item you are claiming really is the same product (or a variation thereof) of something you have claimed before."),
        required=False)

    def __init__(self, user, **kwargs):
        super(ClaimRetailedGearForm, self).__init__(**kwargs)
        self.user = user
        self.fields['make'].choices = [('', '---------')] + sorted(
            uniq(Gear.objects.exclude(make=None).exclude(make='').values_list('make', 'make')),
            key=lambda x: x[0].lower())
        self.fields['merge_with'].choices = \
            [('', '---------')] + \
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


class MergeRetailedGearForm(forms.Form):
    error_css_class = 'error'

    merge_with = forms.ChoiceField(
        choices=[('', '---------')],
        label=_("Merge"),
        help_text=_(
            "Use this field to mark that the item you are merging really is the same product (or a variation thereof) of something you have claimed before."),
        required=False)

    def __init__(self, user, **kwargs):
        super(MergeRetailedGearForm, self).__init__(**kwargs)
        self.fields['merge_with'].choices = \
            [('', '---------')] + \
            uniq_id_tuple(
                RetailedGear.objects.filter(retailer=user).exclude(gear__name=None).values_list('id', 'gear__name'))


class RetailedGearForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = RetailedGear
        fields = ('link', 'price', 'currency')


class CollectionCreateForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Collection
        fields = ('name', 'description',)


class CollectionUpdateForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Collection
        fields = ('name', 'description', 'cover',)


class CollectionAddRemoveImagesForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = Collection
        fields = ('images',)
