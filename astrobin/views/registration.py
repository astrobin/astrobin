import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Fieldset, HTML, Layout
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.views.decorators.http import require_POST
from registration.backends.hmac.views import RegistrationView, ActivationView
from registration.forms import (RegistrationForm, RegistrationFormTermsOfService, RegistrationFormUniqueEmail)
from registration.signals import user_registered

from astrobin.models import UserProfile
from astrobin.utils import get_client_country_code
from astrobin_apps_notifications.services.notifications_service import NotificationContext
from astrobin_apps_notifications.utils import push_notification
from astrobin_apps_users.services import UserService
from common.captcha import TurnstileField
from common.constants import GroupName
from common.services import AppRedirectionService
from common.templatetags.common_tags import button_loading_class, button_loading_indicator

log = logging.getLogger(__name__)


class AstroBinRegistrationForm(RegistrationFormUniqueEmail, RegistrationFormTermsOfService):
    # Keep referral code as hidden field
    referral_code = forms.fields.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )
    
    # Combined communications checkbox
    communications = forms.fields.BooleanField(
        widget=forms.CheckboxInput,
        required=False,
        label=_('Keep me updated with newsletters and important announcements'),
    )
    
    # Captcha for security
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
                'email',
                'password1',
                'password2',
            ),
            Fieldset(
                '',
                'first_name',
                'last_name',
            ),
            Fieldset(
                '',
                'tos',
                'communications',
                'captcha',
            ) if not settings.TESTING else Fieldset(
                '',
                'tos',
                'communications',
            ),
            'referral_code',  # Outside fieldset as a hidden field
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
        
        # Use clear labels and placeholders for all fields
        self.fields['first_name'].label = _('First name')
        self.fields['last_name'].label = _('Last name')
        
        # Simplify the password help texts
        self.fields['password1'].help_text = _('Choose a secure password.')
        self.fields['password2'].help_text = _('Enter the same password again for verification.')
        
        # Update the TOS field label to include the link directly in the label
        self.fields['tos'].label = format_html(
            '{} <a href="https://welcome.astrobin.com/terms-of-service" target="_blank">{}</a>',
            _("I agree to the"),
            _("Terms of Service")
        )
        
        # Remove the help text since the link is now in the label
        self.fields['tos'].help_text = ""

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
        'password1',
        'password2',
        'referral_code',
        'communications',
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
            'username': _('Your public ID and profile URL. Letters, numbers, and ./+/-/_ only.'),
        }


class AstroBinRegistrationView(RegistrationView):
    form_class = AstroBinRegistrationForm
    email_body_template = 'registration/activation_email.txt'
    email_subject_template = 'registration/activation_email_subject.txt'
    html_email_template = 'registration/activation_email.html'

    def dispatch(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            if 'next' in self.request.GET:
                return redirect(self.request.GET['next'])
            else:
                return redirect('/')

        return super().dispatch(*args, **kwargs)
    
    def get_success_url(self, user=None):
        # Instead of relying on the parent class, explicitly use the URL pattern
        from django.urls import reverse
        base_url = reverse('registration_complete')
        
        # Forward the 'next' parameter to the success URL if it exists
        if 'next' in self.request.GET:
            return f"{base_url}?next={self.request.GET['next']}"
        
        return base_url
        
    def get_email_context(self, activation_key):
        context = super().get_email_context(activation_key)
        if 'next' in self.request.GET:
            context['next'] = self.request.GET['next']
        return context
        
    def send_activation_email(self, user):
        """
        Send the activation email. The activation key is the username,
        signed using TimestampSigner.
        """
        activation_key = self.get_activation_key(user)
        context = self.get_email_context(activation_key)
        context.update({
            'user': user,
        })
        subject = render_to_string(self.email_subject_template,
                                   context)
        # Force subject to a single line to avoid header-injection
        # issues.
        subject = ''.join(subject.splitlines())
        
        # Create plain text and HTML message bodies
        message = render_to_string(self.email_body_template, context)
        html_message = None
        if hasattr(self, 'html_email_template'):
            html_message = render_to_string(self.html_email_template, context)
            
        user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL, html_message=html_message)


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

    if 'referral_code' in form.data and form.data['referral_code'] != '':
        profile.referral_code = form.data['referral_code']
        changed = True

    if 'tos' in form.data:
        profile.accept_tos = form.data['tos'] == "on"
        changed = True

    # Use the combined communications field to set all three preferences
    if 'communications' in form.data:
        communications_value = form.data['communications'] == "on"
        profile.receive_important_communications = communications_value
        profile.receive_newsletter = communications_value
        profile.receive_marketing_and_commercial_material = communications_value
        changed = True

    if changed:
        profile.save(keep_deleted=True)

    push_notification([user], None, 'welcome_to_astrobin', {
        'BASE_URL': settings.BASE_URL,
        'extra_tags': {
            'context': NotificationContext.USER
        },
    })


class AstroBinActivationView(ActivationView):
    def get(self, request, activation_key, *args, **kwargs):
        """
        Completely override the get method to handle everything in one step.
        """
        # Activate the user first
        activated_user = self.activate(activation_key=activation_key)
        
        if activated_user:
            # If activation was successful, manually login and create session
            from django.contrib.auth import authenticate, login
            
            # Let's try to authenticate with our special backend method
            user = authenticate(
                request,
                username=activated_user.username,
                password=None,
                _internal_auto_login_for_activated_user=True
            )
            
            if user:
                # Log in the user
                login(request, user)
                
                # Make sure session is saved
                request.session.modified = True
                request.session.save()
                
                success_url = self.get_success_url(request, user)
                
                # Return a redirect response
                from django.http import HttpResponseRedirect
                return HttpResponseRedirect(success_url)

        # If we get here, either activation failed or login failed. Redirect to an error page.
        return redirect(self.get_success_url(request, None))

    def get_success_url(self, request, user):
        next_url = self.request.GET.get('next')

        if next_url:
            return next_url

        if user:
            if AppRedirectionService.should_redirect_to_new_gallery_experience(request):
                return AppRedirectionService.gallery_redirect(request, user.username)
            messages.success(request, _('Your account has been activated.'))
            return reverse('user_page', kwargs={'username': user.username})

        messages.success(request, _('Your account has been activated.'))
        return reverse('auth_login')

    def activate(self, *args, **kwargs):
        """Pass all arguments to the parent's activate method"""
        return super().activate(*args, **kwargs)


@require_POST
def resend_activation_email(request):
    """
    Resends the activation email to a user who just registered.
    Rate limited to once per minute.
    """
    email = request.POST.get('email')
    if not email:
        return JsonResponse({'status': 'error', 'message': _('Email is required.')}, status=400)
    
    try:
        user = User.objects.get(email=email, is_active=False)
    except User.DoesNotExist:
        # Don't reveal if the user exists or not for security reasons
        return JsonResponse({
            'status': 'success',
            'message': _('If the email exists in our system, a new activation email has been sent.')
        })
    
    # Check rate limiting
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    now = timezone.now()
    if profile.last_activation_email_sent and (now - profile.last_activation_email_sent).total_seconds() < 60:
        time_left = 60 - int((now - profile.last_activation_email_sent).total_seconds())
        return JsonResponse({
            'status': 'error', 
            'message': _('Please wait {0} seconds before requesting another email.').format(time_left)
        }, status=429)
    
    # Everything is good, send the email
    # We'll use the RegistrationView's method for getting the activation key
    from registration.backends.hmac.views import RegistrationView
    
    # Get the activation key
    activation_key = RegistrationView().get_activation_key(user)
    
    # Create the context for the email templates
    from django.contrib.sites.shortcuts import get_current_site
    context = {
        'activation_key': activation_key,
        'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
        'site': get_current_site(request),
        'user': user,
    }
    
    # Pass along the 'next' parameter if it exists in the request
    if 'next' in request.POST:
        context['next'] = request.POST.get('next')
    
    # Render the email templates
    subject = render_to_string('registration/activation_email_subject.txt', context)
    subject = ''.join(subject.splitlines())  # Remove newlines
    
    message = render_to_string('registration/activation_email.txt', context)
    html_message = render_to_string('registration/activation_email.html', context)
    
    # Send the email
    user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL, html_message=html_message)
    
    # Update the timestamp
    profile.last_activation_email_sent = now
    profile.save(keep_deleted=True)
    
    return JsonResponse({
        'status': 'success',
        'message': _('A new activation email has been sent to {0}.').format(email)
    })


user_registered.connect(user_created)
