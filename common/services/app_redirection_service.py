from django.http import HttpRequest


class AppRedirectionService:
    def __init__(self):
        pass

    @staticmethod
    def redirect(request, path):
        # type: (HttpRequest) -> str

        host = None
        if 'astrobin.com' in request.META['HTTP_HOST']:
            host = 'app.astrobin.com'
        else:
            host = 'localhost:4400'

        return '{}://{}{}'.format(request.scheme, host, path)
