import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpRequest

from astrobin.enums import ImageEditorStep
from common.constants import GroupName


class AppRedirectionService:
    def __init__(self):
        pass

    @staticmethod
    def redirect(path: str) -> str:
        if settings.BASE_URL in path:
            path = path.replace(settings.BASE_URL, '')

        # from astrobin.middleware.thread_locals_middleware import get_current_user
        # user = get_current_user()
        #
        # def user_id_is_even(user_id: int) -> bool:
        #     return user_id % 2 == 0
        #
        # if (
        #         user and
        #         user.is_authenticated and
        #         user.joined_group_set.filter(name=GroupName.BETA_TESTERS).exists() and
        #         user_id_is_even(user.pk) and
        #         'app.astrobin.com' in settings.APP_URL
        # ):
        #     return f'https://app2.astrobin.com/{path}'

        return f'{settings.APP_URL}{path}'

    @staticmethod
    def contact_redirect(request):
        # type: (HttpRequest) -> unicode

        url = 'https://welcome.astrobin.com/contact'
        user = request.user
        params = {}

        if user.is_authenticated:
            params['username'] = str(user.username).encode('utf-8')
            params['email'] = user.email

        if 'subject' in request.GET:
            params['subject'] = str(urllib.parse.unquote(request.GET.get('subject'))).encode('utf-8')

        if 'message' in request.GET:
            params['message'] = str(urllib.parse.unquote(request.GET.get('message'))).encode('utf-8')

        original_quote_plus = urllib.parse.quote_plus
        urllib.parse.quote_plus = urllib.parse.quote
        query_string = urllib.parse.urlencode(params)
        urllib.parse.quote_plus = original_quote_plus

        if query_string and query_string != '':
            url = url + '?%s' % query_string

        return url

    @staticmethod
    def cookie_domain(request):
        if 'HTTP_HOST' in request.META and 'astrobin.com' in request.META['HTTP_HOST']:
            return '.astrobin.com'

        return 'localhost'

    @staticmethod
    def image_editor_step_number(user: User, step: ImageEditorStep) -> int:

        step_map = {
            ImageEditorStep.BASIC_INFORMATION: 1,
            ImageEditorStep.CONTENT: 2,
            ImageEditorStep.THUMBNAIL: 3,
            ImageEditorStep.WATERMARK: 4,
            ImageEditorStep.EQUIPMENT: 5,
            ImageEditorStep.ACQUISITION: 6,
            ImageEditorStep.SETTINGS: 7,
        }

        try:
            return step_map[step]
        except IndexError:
            return 1

