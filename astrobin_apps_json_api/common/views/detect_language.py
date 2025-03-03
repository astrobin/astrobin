import hashlib
import logging
import simplejson
from braces.views import JSONResponseMixin
from django.core.cache import cache
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

        # Create cache key using an md5 hash of the text
        cache_key = f"lang_detect_{hashlib.md5(text.encode()).hexdigest()}"

        # Try to get the language from cache first
        cached_language = cache.get(cache_key)
        if cached_language:
            return HttpResponse(simplejson.dumps({'language': cached_language}), status=200)

        # Clean the text (remove BBCode) before detection
        cleaned_text = UtilsService.strip_bbcode(text)
        
        # Detect language
        try:
            language = UtilsService.detect_language(cleaned_text)
            
            if language:
                # Cache the result for a long time (30 days)
                cache.set(cache_key, language, 60 * 60 * 24 * 30)
                return HttpResponse(simplejson.dumps({'language': language}), status=200)
            else:
                return HttpResponse(simplejson.dumps({'language': 'unknown'}), status=200)
        except Exception as e:
            log.error(f"Language detection error: {str(e)}")
            return HttpResponse(simplejson.dumps({'error': str(e), 'language': 'unknown'}), status=200)