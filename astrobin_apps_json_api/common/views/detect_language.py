import logging

import simplejson
from braces.views import JSONResponseMixin
from django.http import HttpResponse
from django.views.generic.base import View

from astrobin.services.utils_service import UtilsService

log = logging.getLogger(__name__)


class DetectLanguage(JSONResponseMixin, View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponse(simplejson.dumps({'error': 'Unauthorized'}), status=401)

        data = simplejson.loads(request.body.decode('utf-8'))

        text = data.get('text')

        if not text:
            return HttpResponse(simplejson.dumps({'error': 'Text not provided'}), status=400)

        try:
            language = UtilsService.detect_language(text)
            
            if language:
                return HttpResponse(simplejson.dumps({'language': language}), status=200)
            else:
                return HttpResponse(simplejson.dumps({'language': 'unknown'}), status=200)
        except Exception as e:
            log.error(f"Language detection error: {str(e)}")
            return HttpResponse(simplejson.dumps({'error': str(e), 'language': 'unknown'}), status=200)
