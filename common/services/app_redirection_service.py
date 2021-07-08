import urllib.request, urllib.parse, urllib.error

from django.http import HttpRequest


class AppRedirectionService:
    def __init__(self):
        pass

    @staticmethod
    def redirect(request, path):
        # type: (HttpRequest, str) -> str

        host = None
        if 'HTTP_HOST' in request.META and 'astrobin.com' in request.META['HTTP_HOST']:
            host = 'app.astrobin.com'
        else:
            host = 'localhost:4400'

        return '{}://{}{}'.format(request.scheme, host, path)

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
