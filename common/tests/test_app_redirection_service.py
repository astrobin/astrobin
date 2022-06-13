# -*- coding: utf-8 -*-

import urllib.request, urllib.parse, urllib.error

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase, RequestFactory, override_settings

from astrobin.tests.generators import Generators
from common.services import AppRedirectionService


class AppRedirectionServiceTest(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    @override_settings(APP_URL='http://localhost:4400')
    def test_redirect_from_localhost(self):
        service = AppRedirectionService()
        self.assertEqual('http://localhost:4400/foo', service.redirect('/foo'))

    @override_settings(APP_URL='https://app.astrobin.com')
    def test_redirect_from_astrobin(self):
        service = AppRedirectionService()
        self.assertEqual('https://app.astrobin.com/foo', service.redirect('/foo'))

    @override_settings(APP_URL='https://app.astrobin.com')
    @override_settings(BASE_URL='https://www.astrobin.com')
    def test_redirects_cuts_off_base_url(self):
        service = AppRedirectionService()
        self.assertEqual('https://app.astrobin.com/foo', service.redirect('https://www.astrobin.com/foo'))

    def test_contact_redirect(self):
        request = self.request_factory.get('/contact')
        request.user = AnonymousUser()
        service = AppRedirectionService()

        self.assertEqual('https://welcome.astrobin.com/contact', service.contact_redirect(request))

    def test_contact_redirect_with_user(self):
        request = self.request_factory.get('/contact')
        request.user = Generators.user()
        service = AppRedirectionService()

        url = service.contact_redirect(request)

        self.assertTrue('username=%s' % urllib.parse.quote(str(request.user.username).encode('utf-8')) in url)
        self.assertTrue('email=%s' % urllib.parse.quote(request.user.email) in url)

    def test_contact_redirect_with_user_with_non_ascii_username(self):
        request = self.request_factory.get('/contact')

        user = Generators.user()
        user.username = 'ABCóE'
        user.save()

        request.user = user

        service = AppRedirectionService()

        url = service.contact_redirect(request)

        self.assertTrue('username=%s' % urllib.parse.quote(str(request.user.username).encode('utf-8')) in url)
        self.assertTrue('email=%s' % urllib.parse.quote(request.user.email) in url)

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

        self.assertTrue('username=%s' % urllib.parse.quote(request.user.username) in url)
        self.assertTrue('email=%s' % urllib.parse.quote(request.user.email) in url)
        self.assertTrue('subject=foo' in url)
        self.assertTrue('message=bar' in url)
