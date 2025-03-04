import hashlib
import logging
from datetime import datetime

from google.cloud import translate_v2 as translate
import simplejson
from braces.views import JSONResponseMixin
from django.core.cache import cache
from django.http import HttpResponse
from django.views.generic.base import View
from precise_bbcode.bbcode import get_parser
from rest_framework.authtoken.models import Token

from astrobin.services.utils_service import UtilsService
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free

log = logging.getLogger(__name__)


class Translate(JSONResponseMixin, View):
    # Throttling settings
    FREE_RATE = 100
    PREMIUM_RATE = 500  # Higher limit for premium users
    THROTTLE_PERIOD = 3600  # 1 hour in seconds

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = translate.Client()

    def get_user_rate(self, user):
        valid_subscription = PremiumService(user).get_valid_usersubscription()
        if is_free(valid_subscription):
            return self.FREE_RATE
        return self.PREMIUM_RATE

    def check_throttle(self, user):
        """
        Returns True if request should be throttled (denied).
        Rate depends on subscription status.
        """
        cache_key = f"translate_throttle_{user.id}"
        now = datetime.now().timestamp()

        request_history = cache.get(
            cache_key, {
                'count': 0,
                'reset_time': now + self.THROTTLE_PERIOD
            }
        )

        # Reset if the time period has passed
        if now > request_history['reset_time']:
            request_history = {
                'count': 0,
                'reset_time': now + self.THROTTLE_PERIOD
            }

        # Check if limit exceeded - use appropriate rate based on subscription
        user_rate = self.get_user_rate(user)
        if request_history['count'] >= user_rate:
            return True

        # Increment counter
        request_history['count'] += 1
        cache.set(cache_key, request_history, self.THROTTLE_PERIOD)

        return False

    def get_remaining_requests(self, user):
        """Returns number of remaining requests in current period"""
        cache_key = f"translate_throttle_{user.id}"
        request_history = cache.get(
            cache_key, {
                'count': 0,
                'reset_time': datetime.now().timestamp() + self.THROTTLE_PERIOD
            }
        )

        user_rate = self.get_user_rate(user)
        return max(0, user_rate - request_history['count'])

    def translate_text(self, text: str, source_language: str, target_language: str, format: str):
        result = self.client.translate(
            text,
            source_language=source_language,
            target_language=target_language,
            format_='text'
        )

        translated = result['translatedText']

        if format == 'bbcode':
            parser = get_parser()
            return parser.render(translated)

        return translated

    def post(self, request, *args, **kwargs):
        if 'HTTP_AUTHORIZATION' in request.META:
            token_in_header = request.META['HTTP_AUTHORIZATION'].replace('Token ', '')
            try:
                token = Token.objects.get(key=token_in_header)
                user = token.user
            except Token.DoesNotExist:
                user = None
        else:
            user = request.user

        if user is None or not user.is_authenticated:
            return HttpResponse(simplejson.dumps({'error': 'Unauthorized'}), status=401)

        data = simplejson.loads(request.body.decode('utf-8'))

        text = data.get('text')
        target_language = data.get('target_language')
        source_language = data.get('source_language')
        format_ = data.get('format')

        if not text:
            raise ValueError("Text not provided")

        if not target_language:
            raise ValueError("Target language not provided")

        # If source_language is not provided, use language detection
        if not source_language:
            source_language = 'auto'  # Default to auto if detection fails
            detected_language = UtilsService.detect_language(text)
            if detected_language:
                # If text detection succeeds, use the detected language
                source_language = detected_language
                log.debug(f"Language detected as {detected_language}: {text}")

        if not format_:
            raise ValueError("Format not provided")

        if format_ != 'html' and format_ != 'bbcode':
            raise ValueError("Invalid format")

        cache_key = f"trans_{hashlib.md5((text + source_language + target_language + format_).encode()).hexdigest()}"

        # Try to get the translation from cache first
        cached_translation = cache.get(cache_key)
        if cached_translation:
            # Don't count cached translations against the quota
            translation = cached_translation
        else:
            # Only check throttling for non-cached translations
            if self.check_throttle(user):
                return HttpResponse(
                    simplejson.dumps(
                        {
                            'error': 'Rate limit exceeded',
                            'reset_time': cache.get(f"translate_throttle_{user.id}")['reset_time']
                        }
                    ),
                    status=429
                )

            try:
                translation = self.translate_text(text, source_language, target_language, format_)
                cache.set(cache_key, translation, 86400)
            except Exception as e:
                return HttpResponse(simplejson.dumps({'error': str(e)}), status=400)

        # Include remaining requests info in response
        response_data = {
            'translation': translation,
            'remaining_requests': self.get_remaining_requests(user)
        }

        return HttpResponse(simplejson.dumps(response_data), status=200)
