import string

from django.core.exceptions import ValidationError
from django.utils.translation import gettext


class HasNumbersValidator:
    def validate(self, password: str, user=None):
        if not any(char.isdigit() for char in password):
            raise ValidationError(
                gettext(
                    "This password doesn't contain any numeric digits. It must contain at least one number.",
                ),
                code='password_has_no_numbers',
            )

    def get_help_text(self):
        return gettext("Your password must contain at least one number.")


class HasSpecialCharactersValidator:
    def validate(self, password: str, user=None):
        if not any(c in string.punctuation for c in password):
            raise ValidationError(
                gettext(
                    "This password doesn't contain any special characters. It must contain at least one of the "
                    "following {}".format(string.punctuation),
                ),
                code='password_has_no_numbers',
            )

    def get_help_text(self):
        return gettext(
            "Your password must contain any of the following special characters: {}".format(string.punctuation)
        )


LOGIN_REDIRECT_URL = '/'
ACCOUNT_ACTIVATION_DAYS = 7
AUTH_PROFILE_MODULE = 'astrobin.UserProfile'
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 9,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'astrobin.settings.components.account.HasNumbersValidator',
    },
    {
        'NAME': 'astrobin.settings.components.account.HasSpecialCharactersValidator',
    }
]
AUTHENTICATION_BACKENDS = ('astrobin.auth.CustomBackend', )

