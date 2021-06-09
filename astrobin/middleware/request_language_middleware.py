# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import django
from django.utils import translation
from pybb.compat import is_authenticated

if django.VERSION < (1, 10):  # pragma: no cover
    MiddlewareParentClass = object
else:  # pragma: no cover
    from django.utils.deprecation import MiddlewareMixin

    MiddlewareParentClass = MiddlewareMixin


class RequestLanguageMiddleware(MiddlewareParentClass):
    def process_request(self, request):
        if is_authenticated(request.user) and \
                hasattr(request.user, 'userprofile') and \
                request.user.userprofile.language:
            request.LANGUAGE_CODE = translation.get_language()
        else:
            request.LANGUAGE_CODE = "en"
