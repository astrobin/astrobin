from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Fieldset, HTML, Layout
from django import forms
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from registration.backends.hmac.views import RegistrationView
from registration.forms import (RegistrationForm, RegistrationFormTermsOfService, RegistrationFormUniqueEmail)
from registration.signals import user_registered

from astrobin.models import UserProfile
from astrobin.utils import get_client_country_code
from astrobin_apps_notifications.services.notifications_service import NotificationContext
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_users.services import UserService
from common.captcha import TurnstileField
from common.constants import GroupName
from common.templatetags.common_tags import button_loading_class, button_loading_indicator


class AstroBinRegistrationForm(RegistrationFormUniqueEmail, RegistrationFormTermsOfService):
    skill_level = forms.fields.ChoiceField(
        required=True,
        label=_("Self-assessed skill level"),
        help_text=_("How would you categorize your current skills as an astrophotographer?"),
        choices=((None, "---------"),) + UserProfile.SKILL_LEVEL_CHOICES,
    )

    referral_code = forms.fields.CharField(
        required=False,
        label=_('Referral code') + f' ({_("optional")})',
    )

    important_communications = forms.fields.BooleanField(
        widget=forms.CheckboxInput,
        required=False,
        label=_('I accept to receive rare important communications via email'),
        help_text=_(
            'This is highly recommended. These are very rare and contain information that you probably want to have.'))

    newsletter = forms.fields.BooleanField(
        widget=forms.CheckboxInput,
        required=False,
        label=_('I accept to receive occasional newsletters via email'),
        help_text=_(
            'Newsletters do not have a fixed schedule, but in any case they are not sent out more often than once per month.'))

    marketing_material = forms.fields.BooleanField(
        widget=forms.CheckboxInput,
        required=False,
        label=_('I accept to receive occasional marketing and commercial material via email'),
        help_text=_('These emails may contain offers, commercial news, and promotions from AstroBin or its partners.'))

    captcha = TurnstileField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal form-crispy'
        self.helper.form_method = 'post'
        self.helper.form_action = ''
        self.helper.attrs = {'novalidate': ''}
        self.helper.error_text_inline = False
        self.helper.help_text_inline = False
        self.helper.layout = Layout(
            Fieldset(
                '',
                'username',
                'first_name',
                'last_name',
                'email',
                'skill_level',
            ),
            Fieldset(
                '',
                'password1',
                'password2',
            ),
            Fieldset(
                '',
                'referral_code',
                'tos',
                'important_communications',
                'newsletter',
                'marketing_material',
            ),
            Fieldset(
                '',
                'captcha',
            ) if not settings.TESTING else Fieldset(''),
            Div(
                HTML(
                    f'<button '
                    f'  type="submit" '
                    f'  class="btn btn-primary btn-block-mobile {button_loading_class()}"'
                    f'>'
                    f'  {_("Submit")} {button_loading_indicator()}'
                    f'</button>'
                ),
                css_class='form-actions',
            )
        )

        # For some reason, setting these in `labels` and `help_texts` before doesn't work only for `email`.
        self.fields['email'].label = _('Email address')
        self.fields['email'].help_text = _('AstroBin doesn\'t share your email address with anyone.')

    def clean_referral_code(self):
        value:str = self.cleaned_data.get('referral_code')

        outdated_referral_codes_conversion_map = {
            'NEBULAPHOTOS2021': 'NEBULAPHOTOS',
            'ASTROBACKYARD2021': 'ASTROBACKYARD',
            'ZELINKA2021': 'ZELINKA',
            'INFINITALAVITA2021': 'INFINITALAVITA',
        }

        recognized_referral_codes = (
            'NEBULAPHOTOS',
            'ASTROBACKYARD',
            'ZELINKA',
            'INFINITALAVITA',
            'SIMCUR',
            'SHOTKIT',
        )

        if value in (None, ''):
            return None

        if value.upper() in outdated_referral_codes_conversion_map:
            value = outdated_referral_codes_conversion_map[value.upper()]
        elif value.upper() not in recognized_referral_codes:
            raise forms.ValidationError("This is not one of the recognized referral codes. Please check its spelling!")

        self.data._mutable = True
        self.data['referral_code'] = value.upper()
        self.data._mutable = False

        return value.upper()

    def clean_username(self):
        value: str = self.cleaned_data.get(User.USERNAME_FIELD)
        if value is None:
            return None
        elif "@" in value:
            raise forms.ValidationError(
                _('Sorry, your username cannot contain the "@" character.')
            )
        elif User.objects.filter(username__iexact=value).exists():
            raise forms.ValidationError(
                _('Sorry, this username already exists with a different capitalization.')
            )

        return value

    field_order = [
        'username',
        'first_name',
        'last_name',
        'email',
        'skill_level',
        'password1',
        'password2',
        'referral_code',
        'tos',
        'important_communications',
        'newsletter',
        'marketing_material',
        'captcha',
    ]

    class Meta(RegistrationForm.Meta):
        fields = [
            User.USERNAME_FIELD,
            'email',
            'first_name',
            'last_name',
            'password1',
            'password2'
        ]

        labels = {
            'first_name': _('First name') + f' ({_("optional")})',
            'last_name': _('Last name') + f' ({_("optional")})',
        }

        help_texts = {
            'username': _(
                'This is your handle on AstroBin and will be part of the URL to your gallery. If you do not specify a'
                'first and last name below, it will also be how others see your name. Please use letters, digits, and '
                'the special characters ./+/-/_ only.'
            ),
        }


class AstroBinRegistrationView(RegistrationView):
    form_class = AstroBinRegistrationForm

    def dispatch(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            if 'next' in self.request.GET:
                return redirect(self.request.GET['next'])
            else:
                return redirect('/')

        return super().dispatch(*args, **kwargs)


def user_created(sender, user, request, **kwargs):
    form = AstroBinRegistrationForm(request.POST)
    profile, created = UserProfile.objects.get_or_create(user=user)

    country_code = get_client_country_code(request)

    UserService(profile.user).set_last_seen(country_code)
    UserService(profile.user).set_signup_country(country_code)
    profile.refresh_from_db()

    group, created = Group.objects.get_or_create(name=GroupName.OWN_EQUIPMENT_MIGRATORS)
    user.groups.add(group)
    changed = False

    if 'skill_level' in form.data:
        profile.skill_level = form.data['skill_level']
        changed = True

    if 'referral_code' in form.data and form.data['referral_code'] != '':
        profile.referral_code = form.data['referral_code']
        changed = True

    if 'tos' in form.data:
        profile.accept_tos = form.data['tos'] == "on"
        changed = True

    if 'important_communications' in form.data:
        profile.receive_important_communications = form.data['important_communications'] == "on"
        changed = True

    if 'newsletter' in form.data:
        profile.receive_newsletter = form.data['newsletter'] == "on"
        changed = True

    if 'marketing_material' in form.data:
        profile.receive_marketing_and_commercial_material = form.data['marketing_material'] == "on"
        changed = True

    if changed:
        profile.save(keep_deleted=True)

    push_notification([user], None, 'welcome_to_astrobin', {
        'BASE_URL': settings.BASE_URL,
        'extra_tags': {
            'context': NotificationContext.USER
        },
    })


user_registered.connect(user_created)
