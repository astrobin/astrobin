import urllib.error
import urllib.parse
import urllib.request
from typing import Optional, Union

from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

from astrobin.enums import ImageEditorStep


class AppRedirectionService:
    def __init__(self):
        pass

    @staticmethod
    def redirect(path: str) -> str:
        if settings.BASE_URL in path:
            path = path.replace(settings.BASE_URL, '')

        # from astrobin.middleware.thread_locals_middleware import get_request_cache
        # from common.constants import GroupName
        #
        # user = get_request_cache().get('user', None)
        #
        # if (
        #         user and
        #         user.is_authenticated and
        #         user.joined_group_set.filter(name=GroupName.BETA_TESTERS).exists() and
        #         'localhost' not in settings.APP_URL
        # ):
        #     return f'https://beta-app.astrobin.com/{path}'

        return f'{settings.APP_URL}{path}'

    @staticmethod
    def contact_redirect(request) -> str:
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
    def should_redirect_to_new_gallery_experience(request) -> bool:
        # If we are testing, we don't want to redirect because we want to test the old gallery experience.
        if settings.TESTING:
            return False

        return (
            not request.user.is_authenticated or
            request.user.userprofile.enable_new_gallery_experience
        ) and 'force-classic-view' not in request.GET

    @staticmethod
    def gallery_redirect(request, username) -> str:
        url = AppRedirectionService.redirect(f'/u/{username}')

        if 'staging' in request.GET:
            return url + '#staging'
        elif 'trash' in request.GET:
            return url + '#trash'
        elif 'sub' in request.GET:
            url += f'?folder-type={request.GET.get("sub")}'
            if 'active' in request.GET:
                url += f'&active={request.GET.get("active")}'
            url += '#smart-folders'
            return url

        return url

    @staticmethod
    def search_redirect(query: dict) -> str:
        from astrobin.search import AstroBinSearchView

        url = f'{settings.APP_URL}/search'

        if query:
            url += f'?p={AstroBinSearchView.encode_query_params(query)}'

        return url

    @staticmethod
    def image_redirect(
            request,
            image_id: Union[str, int],
            revision_label: Optional[str] = None,
            comment_id: Optional[int] = None,
    ) -> str:
        if AppRedirectionService.should_redirect_to_new_gallery_experience(request):
            redirect_url = AppRedirectionService.redirect(f'/i/{image_id}')
            if revision_label:
                redirect_url += f'?r={revision_label}'
            if comment_id:
                redirect_url += f'#c{comment_id}'
            return redirect_url

        redirect_url = reverse(
            'image_detail', kwargs={
                'pk': image_id,
                'r': revision_label,
            }
        )
        if comment_id:
            redirect_url += f'#c{comment_id}'
        return redirect_url

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
            
    @staticmethod
    def astrophotographers_list_redirect(request) -> str:
        """
        Redirects to the astrophotographers list in the frontend app
        """
        url = AppRedirectionService.redirect('/explore/astrophotographers-list')
        
        # Preserve query parameters if any
        if request.GET:
            query_params = request.GET.dict()
            query_string = urllib.parse.urlencode(query_params)
            if query_string:
                url = f"{url}?{query_string}"
                
        return url
