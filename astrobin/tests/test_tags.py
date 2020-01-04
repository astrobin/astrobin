# -*- coding: utf-8 -*-

import datetime

from django.test import TestCase

from astrobin.templatetags.tags import date_before, ra_to_hms, dec_to_dms


class TagsTest(TestCase):
    def test_date_before(self):
        d1 = datetime.datetime.now()
        d2 = d1 - datetime.timedelta(days=1)

        self.assertTrue(date_before(d2, d1))

        d2 = d1

        self.assertFalse(date_before(d2, d1))

        d2 = d1 + datetime.timedelta(days=1)

        self.assertFalse(date_before(d2, d1))

    def test_ra_to_hms(self):
        self.assertEqual('3h 22\' 0"', ra_to_hms(50.5))
        self.assertEqual('-3h 22\' 0"', ra_to_hms(-50.5))
        self.assertEqual('10h 20\' 15"', ra_to_hms(155.0625 ))
        self.assertEqual('0h 0\' 0"', ra_to_hms(0))

    def test_dec_to_dms(self):
        self.assertEqual('+50° 30\' 0"', dec_to_dms(50.5))
        self.assertEqual('-50° 30\' 0"', dec_to_dms(-50.5))
        self.assertEqual('+0° 0\' 0"', dec_to_dms(0))
