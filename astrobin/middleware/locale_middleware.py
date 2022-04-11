# -*- coding: utf-8 -*-

from django.utils import translation
from pybb.compat import is_authenticated

from astrobin.middleware.mixins import MiddlewareParentClass


class LocaleMiddleware(MiddlewareParentClass):
    def process_request(self, request):
        if is_authenticated(request.user) and \
                hasattr(request.user, 'userprofile') and \
                request.user.userprofile.language:
            lang: str = request.user.userprofile.language.lower()
            translation.activate(lang)
            request.LANGUAGE_CODE = lang
