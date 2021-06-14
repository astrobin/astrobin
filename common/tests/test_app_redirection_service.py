# -*- coding: utf-8 -*-

import urllib

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory

from astrobin.tests.generators import Generators
from common.services import AppRedirectionService


class AppRedirectionServiceTest(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def test_redirect_from_localhost(self):
        request = self.request_factory.get('/')
        service = AppRedirectionService()

        request.META['HTTP_HOST'] = 'localhost:8083'
        self.assertEquals('http://localhost:4400/foo', service.redirect(request, '/foo'), )

    def test_redirect_from_astrobin(self):
        request = self.request_factory.get("/")
        service = AppRedirectionService()

        request.META['HTTP_HOST'] = 'www.astrobin.com   '
        self.assertEquals('http://app.astrobin.com/foo', service.redirect(request, '/foo'), )

    def test_contact_redirect(self):
        request = self.request_factory.get('/contact')
        request.user = AnonymousUser()
        service = AppRedirectionService()

        self.assertEquals(u'https://welcome.astrobin.com/contact', service.contact_redirect(request))

    def test_contact_redirect_with_user(self):
        request = self.request_factory.get('/contact')
        request.user = Generators.user()
        service = AppRedirectionService()

        url = service.contact_redirect(request)

        self.assertTrue('username=%s' % urllib.quote(unicode(request.user.username).encode('utf-8')) in url)
        self.assertTrue('email=%s' % urllib.quote(request.user.email) in url)

    def test_contact_redirect_with_user_with_non_ascii_username(self):
        request = self.request_factory.get('/contact')

        user = Generators.user()
        user.username = u'ABCóE'
        user.save()

        request.user = user

        service = AppRedirectionService()

        url = service.contact_redirect(request)

        self.assertTrue('username=%s' % urllib.quote(unicode(request.user.username).encode('utf-8')) in url)
        self.assertTrue('email=%s' % urllib.quote(request.user.email) in url)

    def test_contact_redirect_with_request_data(self):
        request = self.request_factory.get('/contact')
        request.user = AnonymousUser()
        request.GET = {
            'subject': 'foo',
            'message': 'bar'
        }
        service = AppRedirectionService()

        url = service.contact_redirect(request)

        self.assertTrue('subject=foo' in url)
        self.assertTrue('message=bar' in url)

    def test_contact_redirect_with_user_and_request_data(self):
        request = self.request_factory.get('/contact')
        request.user = Generators.user()
        request.GET = {
            'subject': 'foo',
            'message': 'bar'
        }
        service = AppRedirectionService()

        url = service.contact_redirect(request)

        self.assertTrue('username=%s' % urllib.quote(request.user.username) in url)
        self.assertTrue('email=%s' % urllib.quote(request.user.email) in url)
        self.assertTrue('subject=foo' in url)
        self.assertTrue('message=bar' in url)
