from enum import Enum

from django.utils.translation import gettext_lazy as _


class CookieGroupName(Enum):
    ESSENTIAL = _('Essential cookies')
    FUNCTIONAL = _('Functional cookies (recommended)')
    PERFORMANCE = _('Performance cookies (recommended)')
    ANALYTICS = _('Analytics cookies')
    ADVERTISING = _('Advertising cookies')
