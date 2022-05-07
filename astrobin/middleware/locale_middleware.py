# -*- coding: utf-8 -*-
from typing import Optional

from django.utils import translation
from django.utils.translation import get_language_from_request
from pybb.compat import is_authenticated

from astrobin.middleware.mixins import MiddlewareParentClass


class LocaleMiddleware(MiddlewareParentClass):
    def process_request(self, request):
        language: Optional[str] = None
        request_language: Optional[str] = get_language_from_request(request)

        if is_authenticated(request.user) and hasattr(request.user, 'userprofile'):
            if request.user.userprofile.language:
                language = request.user.userprofile.language.lower()
            else:
                request.user.userprofile.language = request_language
                request.user.userprofile.save(keep_deleted=True)

        if language:
            request.LANGUAGE_CODE = language
            if language != request_language:
                translation.activate(language)
