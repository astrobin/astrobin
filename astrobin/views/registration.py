from __future__ import absolute_import

# Python
from datetime import datetime

# Django
from django import forms
from django.utils.translation import ugettext_lazy as _

# 3rd party
from registration.backends.hmac.views import RegistrationView
from registration.forms import (
    RegistrationFormUniqueEmail, RegistrationFormTermsOfService)
from registration.signals import user_registered

# AstroBin
from astrobin.models import UserProfile


class AstroBinRegistrationForm(RegistrationFormUniqueEmail,
                               RegistrationFormTermsOfService):
    important_communications = forms.fields.BooleanField(
        widget=forms.CheckboxInput,
        required=False,
        label=_(u'I accept to receive rare important communications via email'),
        help_text=_(u'This is highly recommended. These are very rare and contain information that you probably want to have.'))

    newsletter = forms.fields.BooleanField(
        widget=forms.CheckboxInput,
        required=False,
        label=_(u'I accept to receive occasional newsletters via email'),
        help_text=_(u'Newsletters do not have a fixed schedule, but in any case they are not sent out more often than once per month.'))

    marketing_material = forms.fields.BooleanField(
        widget=forms.CheckboxInput,
        required=False,
        label=_(u'I accept to receive occasional marketing and commercial material via email'),
        help_text=_(u'These emails may contain offers, commercial news, and promotions from AstroBin or its partners.'))


class AstroBinRegistrationView(RegistrationView):
    form_class = AstroBinRegistrationForm


def user_created(sender, user, request, **kwargs):
    form = AstroBinRegistrationForm(request.POST)
    profile, created = UserProfile.objects.get_or_create(user=user)
    changed = False

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


user_registered.connect(user_created)
