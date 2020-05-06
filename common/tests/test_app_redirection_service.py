from django.test import TestCase, RequestFactory

from common.services import AppRedirectionService


class AppRedirectionServiceTest(TestCase):
    def test_redirect_from_localhost(self):
        request = RequestFactory().get('/')
        service = AppRedirectionService()

        request.META['HTTP_HOST'] = 'localhost:8083'
        self.assertEquals('http://localhost:4400/foo', service.redirect(request, '/foo'), )

    def test_redirect_from_astrobin(self):
        request = RequestFactory().get("/")
        service = AppRedirectionService()

        request.META['HTTP_HOST'] = 'www.astrobin.com   '
        self.assertEquals('http://app.astrobin.com/foo', service.redirect(request, '/foo'), )
