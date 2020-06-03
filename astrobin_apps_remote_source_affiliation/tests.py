# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.test import TestCase
from mock import patch

from astrobin_apps_remote_source_affiliation.models import RemoteSourceAffiliate
from astrobin_apps_remote_source_affiliation.templatetags.astrobin_apps_remote_source_affiliation_tags import \
    is_remote_source_affiliate, remote_source_affiliate_url


class RemoteSourceAffiliateTest(TestCase):
    def test_is_remote_source_affiliate_when_none(self):
        self.assertFalse(is_remote_source_affiliate("foo"))

    def test_is_remote_source_affiliate_when_not_affiliate(self):
        RemoteSourceAffiliate(
            code="foo",
            name="foo",
            url="http://example.com"
        ).save()
        self.assertFalse(is_remote_source_affiliate("foo"))

    @patch("common.services.DateTimeService.today")
    def test_is_remote_source_affiliate_when_expired(self, today):
        RemoteSourceAffiliate(
            code="foo",
            name="foo",
            url="http://example.com",
            affiliation_start=datetime.date(2000, 1, 1),
            affiliation_expiration=datetime.date(2001, 1, 1),
        ).save()
        today.return_value = datetime.date(2001, 2, 1)
        self.assertFalse(is_remote_source_affiliate("foo"))

    @patch("common.services.DateTimeService.today")
    def test_is_remote_source_affiliate_when_not_expired(self, today):
        RemoteSourceAffiliate(
            code="foo",
            name="foo",
            url="http://example.com",
            affiliation_start=datetime.date(2000, 1, 1),
            affiliation_expiration=datetime.date(2001, 1, 1),
        ).save()
        today.return_value = datetime.date(2000, 2, 1)
        self.assertTrue(is_remote_source_affiliate("foo"))

    def test_remote_source_affiliate_url(self):
        RemoteSourceAffiliate(
            code="foo",
            name="doo",
            url="http://example.com"
        ).save()
        self.assertEquals(remote_source_affiliate_url("foo"), "http://example.com")
