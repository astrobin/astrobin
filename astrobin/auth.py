from annoying.functions import get_object_or_None
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.utils.translation import gettext


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].label =gettext("Username or email")
        self.fields["username"].help_text = gettext(
            "Please note: this is your username or email address, not your real name or display name that you might "
            "have set in your AstroBin settings."
        )

# Class to permit the authentication using email or username, with case sensitive and insensitive matches.
class CustomBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        case_sensitive = UserModel.objects.filter(Q(username__exact=username) | Q(email__iexact=username)).distinct()
        case_insensitive = UserModel.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).distinct()
        user = None

        if case_sensitive.exists():
            user = case_sensitive.first()
        elif case_insensitive.exists():
            count = case_insensitive.count()

            if count == 1:
                user = case_insensitive.first()

        if user and user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        return get_object_or_None(get_user_model(), pk=user_id)
