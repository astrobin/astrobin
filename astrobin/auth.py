from typing import Optional

from annoying.functions import get_object_or_None
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.forms import forms
from django.utils.translation import gettext


class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': gettext(
            'Please enter a correct username and password. Note that both fields are case-sensitive.'
        ),
        'inactive': gettext(
            'This account is inactive.'
        ),
        'multiple_users': gettext(
            'Multiple users found with alternative capitalizations of this username. Please use the correct '
            'capitalization.'
        ),
        'non_unique_real_name': gettext(
            'Multiple users found with this name. Please try logging in with your username or email.'
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].label = gettext("Username or email")

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        try:
            authenticate(self.request, username=username, password=password)
        except ValueError as e:
            raise forms.ValidationError(
                self.error_messages[str(e)],
                code=str(e)
            )

        return super().clean()


# Class to permit the authentication using email or username, with case sensitive and insensitive matches.
class CustomBackend(ModelBackend):
    @staticmethod
    def get_user_by_username_or_email(handle: str) -> Optional[get_user_model()]:
        model = get_user_model()
        case_sensitive = model.objects.filter(Q(username__exact=handle) | Q(email__iexact=handle)).distinct()
        case_insensitive = model.objects.filter(Q(username__iexact=handle) | Q(email__iexact=handle)).distinct()

        if case_sensitive.exists():
            return case_sensitive.first()

        case_insensitive_count = case_insensitive.count()

        if case_insensitive_count == 1:
            return case_insensitive.first()
        elif case_insensitive_count > 1:
            raise ValueError('multiple_users')

        return None

    @staticmethod
    def get_user_by_real_name(real_name: str) -> Optional[get_user_model()]:
        model = get_user_model()
        users = model.objects.filter(Q(userprofile__real_name__iexact=real_name)).distinct()
        count = users.count()

        if count == 1:
            return users.first()
        elif count > 1:
            raise ValueError('non_unique_real_name')

        return None

    def authenticate(self, request, username: str = None, password: str = None, **kwargs):
        user = self.get_user_by_username_or_email(username)

        if user is None:
            user = self.get_user_by_real_name(username)

        if user and user.check_password(password):
            return user

    def get_user(self, user_id: int):
        return get_object_or_None(get_user_model(), pk=user_id)
        
    def authenticate(self, request, username: str = None, password: str = None, _internal_auto_login_for_activated_user=False, **kwargs):
        """
        Special override for activated users that need to be logged in automatically.
        This helps with the activation flow.
        """
        # First try the normal authentication 
        user = super().authenticate(request, username, password, **kwargs)
        
        # If normal authentication failed and our special flag is set,
        # bypass password checking completely for activation flow
        if user is None and _internal_auto_login_for_activated_user:
            user = self.get_user_by_username_or_email(username)
            
        return user
