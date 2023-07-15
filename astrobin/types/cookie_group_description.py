from enum import Enum

from django.utils.translation import gettext_lazy as _


class CookieGroupDescription(Enum):
    ESSENTIAL = _(
        'These cookies are essential for the website to function properly.'
    )
    FUNCTIONAL = _(
        'These cookies are used to provide additional functionality to the website, such as remembering local '
        'preferences.',
    )
    PERFORMANCE = _(
        'These cookies are used to improve the website performance by saving some pieces of information on your '
        'computer and avoiding reading from the AstroBin database when possible.'
    )
    ANALYTICS = _(
        'These cookies are used to anonymously track your usage of the website, so that we can improve it over time.'
    )
    ADVERTISING = _(
        'These cookies are used to honor ad display frequency caps. AstroBin does NOT serve targeted ads.'
    )
