# Python

# Django
from django import forms
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

# This app
from .models import (
    PublicDataPool,
    PrivateSharedFolder,
)


class PublicDataPoolForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = PublicDataPool
        fields = ('name', 'description',)


class PublicDataPool_SelectExistingForm(forms.Form):
    error_css_class = 'error'

    existing_pools = forms.ChoiceField(
        label='',
        choices=[],
    )

    def __init__(self, **kwargs):
        super(PublicDataPool_SelectExistingForm, self).__init__(**kwargs)
        # Init choices here to prevent stagnation due to django caching.
        self.fields['existing_pools'].choices = PublicDataPool.objects.all().values_list('id', 'name')


class PublicDataPool_ImagesForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = PublicDataPool
        fields = ('images',)


class PrivateSharedFolderForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = PrivateSharedFolder
        fields = ('name', 'description',)


class PrivateSharedFolder_SelectExistingForm(forms.Form):
    error_css_class = 'error'

    existing_folders = forms.ChoiceField(
        label='',
        choices=[],
    )

    def __init__(self, user, **kwargs):
        super(PrivateSharedFolder_SelectExistingForm, self).__init__(**kwargs)
        # Init choices here to prevent stagnation due to django caching.
        folders = PrivateSharedFolder.objects.filter(
            Q(creator=user) |
            Q(users=user)).values_list('id', 'name')
        self.fields['existing_folders'].choices = folders


class PrivateSharedFolder_ImagesForm(forms.ModelForm):
    error_css_class = 'error'

    class Meta:
        model = PrivateSharedFolder
        fields = ('images',)


class PrivateSharedFolder_UsersForm(forms.ModelForm):
    error_css_class = 'error'

    users = forms.CharField(
        label=_("Users"),
        help_text=_("A list of users you want to invite. Use a comma to separate them."),
        widget=forms.TextInput(attrs={
            'data-provide': 'typeahead',
        })
    )

    class Meta:
        model = PrivateSharedFolder
        fields = ()
